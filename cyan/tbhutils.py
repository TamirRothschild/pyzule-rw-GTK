import os
import sys
import shutil
import zipfile
import platform
import plistlib
import subprocess
from glob import glob
from argparse import Namespace
from importlib import resources  # type: ignore
from typing import Optional, Any
from tempfile import TemporaryDirectory


def validate_inputs(args: Namespace) -> Optional[str]:
  if not (
      args.i.endswith(".ipa")
      or args.i.endswith(".app")
  ):
    return "the input file must be an ipa/app"

  if not os.path.exists(args.i):
    return f"{args.i} does not exist"

  if os.path.exists(args.o):
    try:
      overwrite = input(
        f"[<] {args.o} already exists, overwrite it? [Y/n] "
        if args.output is not None
        else "[<] no output was specified. overwrite the input? [Y/n] "
      ).strip().lower()
    except KeyboardInterrupt:
      sys.exit("[>] bye!")

    if overwrite not in ("y", "yes", ""):
      print("[>] quitting.")
      sys.exit(0)

  if args.f is not None:
    # dictionary ensures unique names
    args.f = {os.path.basename(f): os.path.normpath(f) for f in args.f}
    nonexistent = [f for f in args.f.values() if not os.path.exists(f)]

    if len(nonexistent) != 0:
      print("[!] please ensure the following file(s) exist:")
      for ne in nonexistent:
        print(f"[?] - {ne}")
      sys.exit(1)


def get_app(path: str, tmpdir: str, is_ipa: bool) -> tuple[str, str]:
  payload = f"{tmpdir}/Payload"

  if is_ipa:
    print("[*] extracting ipa..")

    try:
      with zipfile.ZipFile(path) as ipa:
        names = ipa.namelist()

        if not any(name.startswith("Payload/") for name in names):
          raise KeyError
        elif not any(name.endswith(".app/Info.plist") for name in names):
          sys.exit("[!] no Info.plist, invalid app")

        ipa.extractall(tmpdir)
        app = glob(f"{payload}/*.app")[0]
        plist = f"{app}/Info.plist"
    except (KeyError, IndexError):
      sys.exit("[!] couldn't find either Payload or app folder, invalid ipa")
    except zipfile.BadZipFile:
      sys.exit(f"[!] {path} is not a zipfile (ipa)")

    print("[*] extracted ipa")
  else:
    if not os.path.isfile((plist := f"{path}/Info.plist")):
      sys.exit("[!] no Info.plist, invalid app")

    print("[*] copying app..")
    shutil.copytree(path, (app := f"{payload}/{os.path.basename(path)}"))
    print("[*] copied app")

  return app, plist


def get_tools_dir() -> tuple[str, str]:
  mach = platform.machine()
  system = platform.system()

  if "iPhone" in mach or "iPad" in mach:
    mach = "iOS"

  with resources.files() as files:  # type: ignore
    return (
      str(files),  # type: ignore
      str(files / "tools" / system / mach)  # type: ignore
    )


def get_plist(path: str) -> dict[str, Any]:
  try:
    with open(path, "rb") as f:
      return plistlib.load(f)
  except Exception:
    sys.exit(f"[!] couldn't read {path}")


def delete_if_exists(path: str, bn: str) -> bool:
  is_file = os.path.isfile(path)

  try:
    if is_file:
      os.remove(path)
    else:
      shutil.rmtree(path)

    print(f"[?] {bn} already existed, replacing")
    return True
  except FileNotFoundError:
    return False


def extract_deb(deb: str, tweaks: dict[str, str], tmpdir: str) -> None:
  with TemporaryDirectory(prefix=tmpdir + "/", delete=False) as t2:
    if platform.system() == "Linux":
      tool = ["ar", "-x", deb, f"--output={t2}"]
    else:
      tool = ["tar", "-xf", deb, f"--directory={t2}"]

    try:
      subprocess.run(tool, check=True)
    except Exception:
      sys.exit(f"[!] couldn't extract {os.path.basename(deb)}")

    # it's not always "data.tar.gz"
    data_tar = glob(f"{t2}/data.*")[0]
    subprocess.run(["tar", "-xf", data_tar, f"--directory={t2}"])

    for hi in sum((
        glob(f"{t2}/**/*.dylib", recursive=True),
        glob(f"{t2}/**/*.bundle", recursive=True),
        glob(f"{t2}/**/*.appex", recursive=True),
        glob(f"{t2}/**/*.framework", recursive=True)
    ), []):  # type: ignore
      if os.path.islink(hi):
        continue  # symlinks are broken iirc

      tweaks[os.path.basename(hi)] = hi

    print(f"[*] extracted {os.path.basename(deb)}")
    del tweaks[deb]
