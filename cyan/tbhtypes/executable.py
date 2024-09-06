import os
import sys
import shutil
import subprocess
from typing import Optional

try:
  import lief
except Exception:
  pass

from cyan import tbhutils


class Executable:
  install_dir, specific = tbhutils.get_tools_dir()
  nt = f"{specific}/install_name_tool"
  ldid = f"{specific}/ldid"
  lipo = f"{specific}/lipo"
  otool = f"{specific}/otool"

  starters = ("\t/Library/", "\t@rpath", "\t@executable_path")

  def __init__(self, path: str, bundle_path: Optional[str] = None):
    if not os.path.isfile(path):
      sys.exit(f"[!] {path} does not exist (executable)")

    self.path = path
    self.bundle_path = bundle_path

    self.bn = os.path.basename(path)
    self.inj: Optional = None  # type: ignore

    if self.specific.endswith("iOS"):
      self.inj_func = self.ios_inject
    else:
      self.inj_func = self.insert_cmd

  def is_encrypted(self) -> bool:
    proc = subprocess.run(
      [self.otool, "-l", self.path],
      capture_output=True
    )

    return b"cryptid 1" in proc.stdout

  def inject(self, tweaks: dict[str, str], tmpdir: str) -> None:
    # we only inject into the main executable
    assert self.bundle_path is not None

    has_entitlements = False
    ENT_PATH = f"{self.bundle_path}/cyan.entitlements"
    PLUGINS_DIR = f"{self.bundle_path}/PlugIns"
    FRAMEWORKS_DIR = f"{self.bundle_path}/Frameworks"

    with open(ENT_PATH, "wb") as entf:
      proc = subprocess.run(
        [self.ldid, "-e", self.path],
        capture_output=True
      )

      entf.write(proc.stdout)

    if os.path.getsize(ENT_PATH) > 0:
      has_entitlements = True

    # iirc, injecting doesnt work (sometimes) if the file isn't signed
    self.fakesign(False)

    if any(t.endswith(".appex") for t in tweaks):
      os.makedirs(PLUGINS_DIR, exist_ok=True)

    if any(
        t.endswith(k)
        for t in tweaks
        for k in (".deb", ".dylib", ".framework")
    ):
      os.makedirs(FRAMEWORKS_DIR, exist_ok=True)

      # some apps really dont have this lol
      subprocess.run(
        [self.nt, "-add_rpath", "@executable_path/Frameworks", self.path],
        stderr=subprocess.DEVNULL
      )

    # need ~~two~~ THREE loops, one for copying all files to tmpdir
    print("[*] preparing; this may take a while, sorry")
    for bn, path in dict(tweaks).items():
      if bn.endswith(".deb"):
        tbhutils.extract_deb(path, tweaks, tmpdir)
        continue

      try:
        tweaks[bn] = shutil.copytree(path, f"{tmpdir}/{bn}")
      except NotADirectoryError:
        tweaks[bn] = shutil.copy2(path, tmpdir)

      # print(f"[*] prepared {bn}")

    needed: set[str] = set()
    common = {
      # substrate could show up as
      # CydiaSubstrate.framework, libsubstrate.dylib, CydiaSubstrate.dylib
      # and probably even more. it's crazy.

      "substrate.": "CydiaSubstrate.framework",
      "Orion.framework": "Orion.framework",
      "Cephei.framework": "Cephei.framework",
      "CepheiUI.framework": "CepheiUI.framework",
      "CepheiPrefs.framework": "CepheiPrefs.framework"
    }

    # another loop for fixing dylib dependencies
    for dbn, path in tweaks.items():
      if not dbn.endswith(".dylib"):
        continue

      dylib = Executable(path)
      dylib.fakesign()

      # fix dependencies
      for dep in dylib.get_dependencies():
        for cname in (tweaks | common):
          if cname in dep:
            # i wonder if there's a better way to do this?
            if cname.endswith(".framework"):
              npath = f"@rpath/{cname}/{cname[:-10]}"
            else:
              npath = f"@rpath/{cname}"

            if cname in common:
              needed.add(cname)

            if dep != npath:
              dylib.change_dependency(dep, npath)
              print(f"[*] fixed dependency in {dbn}: {dep} -> {npath}")

    # orion has a *weak* dependency to substrate,
    # but will still crash without it. nice !!!!!!!!!!!
    if "Orion.framework" in needed:
      needed.add("substrate.")

    for missing in needed:
      real = common[missing]  # "real" name, thanks substrate!
      ip = f"{FRAMEWORKS_DIR}/{real}"
      existed = tbhutils.delete_if_exists(ip, real)
      shutil.copytree(f"{self.install_dir}/extras/{real}", ip)

      if not existed:
        print(f"[*] auto-injected {real}")

    # and FINALLY, one for actually injecting
    for bn, path in tweaks.items():
      if bn.endswith(".appex"):
        fpath = f"{PLUGINS_DIR}/{bn}"
        existed = tbhutils.delete_if_exists(fpath, bn)
        shutil.copytree(path, fpath)
      elif bn.endswith(".dylib"):
        fpath = f"{FRAMEWORKS_DIR}/{bn}"
        existed = tbhutils.delete_if_exists(fpath, bn)
        self.inj_func(f"@rpath/{bn}")
        shutil.copy2(path, FRAMEWORKS_DIR)
      elif bn.endswith(".framework"):
        fpath = f"{FRAMEWORKS_DIR}/{bn}"
        existed = tbhutils.delete_if_exists(fpath, bn)
        self.inj_func(f"@rpath/{bn}/{bn[:-10]}")
        shutil.copytree(path, fpath)
      else:
        fpath = f"{self.bundle_path}/{bn}"
        existed = tbhutils.delete_if_exists(fpath, bn)
        try:
          shutil.copytree(path, fpath)
        except NotADirectoryError:
          shutil.copy2(path, self.bundle_path)

      if not existed:
        print(f"[*] injected {bn}")

    # FINALLY !!
    if self.inj is not None:  # type: ignore
      self.inj.write(self.path)  # type: ignore

    if has_entitlements:
      subprocess.run(["ldid", f"-S{ENT_PATH}", self.path])
      print("[*] restored entitlements")

  def fakesign(self, keep_entitlements: bool = True) -> bool:
    cmd = [self.ldid, "-S"]
    if keep_entitlements:
      cmd.append("-M")

    subprocess.run(cmd + [self.path])
    return True

  def thin(self) -> bool:
    if subprocess.run(
        [self.lipo, "-thin", "arm64", self.path, "-output", self.path],
        stderr=subprocess.DEVNULL
    ).returncode == 0:
      return True

    return False

  def change_dependency(self, old: str, new: str) -> None:
    subprocess.run([self.nt, "-change", old, new, self.path])

  def insert_cmd(self, cmd: str) -> None:
    if self.inj is None:  # type: ignore
      try:
        lief.logging.disable()  # type: ignore
      except Exception:
        sys.exit("[!] did you forget to install lief?")

      self.inj = lief.parse(self.path)  # type: ignore

    self.inj.add(lief.MachO.DylibCommand.weak_lib(cmd))  # type: ignore

  def ios_inject(self, cmd: str) -> None:
    subprocess.run(
      [
        f"{self.specific}/insert_dylib",
        "--weak", "--inplace", "--no-strip-codesig", "--all-yes",
        cmd, self.path
      ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

  def get_dependencies(self) -> list[str]:
    proc = subprocess.run(
      [self.otool, "-L", self.path],
      capture_output=True, text=True
    )

    # split at [2:] to avoid otool's line and dylib's id
    tmp = proc.stdout.strip().split("\n")[2:]
    for ind, dep in enumerate(tmp):
      if "(architecture " in dep:  # avoid checking duplicate deps
        tmp = tmp[:ind]

    deps: list[str] = []
    for dep in tmp:
      if any(dep.startswith(s) for s in self.starters):
        deps.append(dep.split()[0])  # split() removes whitespace

    return deps

