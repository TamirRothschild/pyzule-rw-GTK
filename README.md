# pyzule-rw / cyan (with a GUi)

a rewrite of [pyzule](https://github.com/asdfzxcvbn/pyzule) that doesn't (completely) suck !!

## features

you can open an issue to request a feature :D !! also see my [recommended flags](https://github.com/asdfzxcvbn/pyzule-rw/wiki/recommended-flags)

- generate and use shareable .cyan files to configure IPAs!
- inject deb, dylib, framework, bundle, and appex files/folders
- automatically fix dependencies on CydiaSubstrate **(cyan uses [ElleKit](https://github.com/evelyneee/ellekit/)!)**, Cephei*, and Orion
- copy any unknown file/folder types to app root
- change app name, version, bundle id, and minimum os version
- remove UISupportedDevices
- remove watch app
- change the app icon
- fakesign the output ipa/tipa/app
- add custom entitlements to the main executable
- thin all binaries to arm64, it can LARGELY reduce app size sometimes!
- remove all app extensions (or just encrypted ones!)

## install instructions

cyan supports **linux, macOS, WSL, and jailbroken iOS!** all either x86_64 or arm64/aarch64 !!

first, make sure you have [ar](https://command-not-found.com/ar) and [tar](https://command-not-found.com/tar) installed

also obviously install python, version 3.9 or greater is required

the `zip` and `unzip` commands are *optional* dependencies, they may [fix issues when extracting certain IPAs with chinese characters](https://github.com/asdfzxcvbn/pyzule-rw/wiki/file-does-not-exist-(executable)-%3F), etc

<details>
<summary><b>linux/WSL/macOS instructions</b></summary>
<br/>
<ol>
  <li>install <a href="https://github.com/pypa/pipx?tab=readme-ov-file#install-pipx">pipx</a></li>
  <li>install OR update cyan: <code>pipx install --force https://github.com/asdfzxcvbn/pyzule-rw/archive/main.zip</code></li>
  <li><b>if you want to inject dylibs ON AARCH64 LINUX</b>: <code>pipx inject cyan lief</code></li>
  <li><b>if you want to change app icons (iOS NOT supported)</b>: <code>pipx inject cyan Pillow</code></li>
</ol>
</details>

<details>
<summary><b>jailbroken iOS instructions / automated environment (github workflow, etc)</b></summary>
<br/>
<ol>
  <li>install OR update cyan: <code>pip install --force-reinstall https://github.com/asdfzxcvbn/pyzule-rw/archive/main.zip</code></li>
</ol>
</details>

<details>
<summary><b>Quick script to install Cyan & Cyan-GUi-GTK</b></summary>
<br/>
<ol>
  <li> This will install and will help you find the missing dependencies, yet; make sure you have: <code>curl gcc pipx pkg-config gtk+-3.0</code></li>
  <li> Then at last run this script (you can review it if you wish) and sit back 
    
    curl -sL https://raw.githubusercontent.com/TamirRothschild/pyzule-rw-GTK/refs/heads/main/cyan/GTK/install-cyan-full-on-gui.sh | bash
  <a>Remmber!! DONT RUN A SCRIPT BEFORE YOU HAVE READ IT AND YOU TRUST IT TO DO NO HARM</a>
</ol>
</details>

## The GUi
###### simple to master
<img src="https://github.com/user-attachments/assets/7d35d201-e1b5-44df-b2a8-97c09ab63881" width="auto" height="50%" />

## making cyan files

cyan comes bundled with the `cgen` command, which lets you generate `.cyan` files to pass to `-z`/`--cyan` !

## acknowledgements

- [Al4ise](https://github.com/Al4ise) for the original [Azule](https://github.com/Al4ise/Azule)
- [lief-project](https://github.com/lief-project) for [LIEF](https://github.com/lief-project/LIEF)
- [tyilo](https://github.com/tyilo) for [insert_dylib](https://github.com/tyilo/insert_dylib/) (macOS/iOS)
- [LeanVel](https://github.com/LeanVel) for [insert_dylib](https://github.com/LeanVel/insert_dylib) (linux)

