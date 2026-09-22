# Building a standalone macOS release

The new packaged app bundles Python, NumPy, SciPy, PyObjC, FFmpeg and FFprobe. It
runs a native macOS menu/Dock application and opens its interface in your browser.
The older AppleScript app in the source folder is only a development launcher;
release apps are the ones produced under `dist-ARCH` by this build. The builder prints its final app path.

Use macOS 14 or newer and Python 3.14 for the target architecture. Apple command
line development tools and pkg-config are build prerequisites; users installing
the finished application do not need them. Intel x264 assembly also needs NASM.

```bash
python3 -m venv build-venv
build-venv/bin/python -m pip install -r packaging/build-requirements.txt
build-venv/bin/python packaging/build_release.py --work-dir /path/with/10GB/free
```

Use an arm64 Python for Apple silicon and an x86_64 Python on Intel or Rosetta for
Intel. The build uses `platform.machine()` and PyInstaller verifies native library
architecture. Separate packages are produced; no universal2 claim is made. Run the
same test suite on each architecture and supported macOS version before publishing.
The numerical-library wheels impose a macOS 14 minimum; the bundled FFmpeg is
compiled with a macOS 13 deployment target and links only Apple system libraries.
Do not replace it with a Homebrew FFmpeg build, which can require a newer macOS and
Homebrew dylibs absent on another person's Mac.

`build_ffmpeg.sh` downloads a pinned official FFmpeg 9.0.1 source archive (SHA256
verified) and a pinned x264 source commit. It disables external library autodetection,
compiles x264 statically, enables built-in decoders/filters/parsers, and includes the
output codecs used by Studio. Source archives and the exact configure recipe are
included in the Sources ZIP next to each binary package. Never omit that ZIP when
redistributing the included GPL FFmpeg/x264 binaries.

The builder verifies Mach-O dependencies have no build-machine/Homebrew paths,
checks the app's signature, makes a real installation copy with `ditto`, then checks
the copied app's signature and runs an H.264/AAC/scientific-runtime self-test with
Homebrew absent from PATH. AppleDouble metadata from exFAT build disks is excluded
before signing, so installation cannot invalidate the resource seal. Outputs: `.app`, `.zip`, `.dmg`, source ZIP, a build report,
and SHA256 checksums. When the work disk is exFAT, the builder creates and mounts
an APFS sparse disk image inside the work directory for bundle/signature metadata.
The image remains mounted so the built app can be tested; eject it after testing.
`--bundle-dir /an/APFS/path` overrides that location. Install the app on your Mac's
Applications folder rather than extracting it onto an exFAT drive. ZIP and DMG
release files can safely be stored on exFAT.

`--skip-ffmpeg` reuses a previously compiled runtime when
iterating on application code. `--skip-dmg` creates ZIP artifacts only.

## Sign and package without notarization

`sign_release.py` signs an existing verified app copy with a local Developer ID
Application certificate, then creates a signed DMG and a ZIP containing the signed
app. It never submits to Apple for notarization. It verifies each runtime component,
secure timestamps, the hardened runtime on executables, target architecture, and
actual installations from both DMG and ZIP, including an H.264/AAC runtime test.
Use fresh staging directories on local APFS. Do not pass the installed app.

```bash
python3 packaging/sign_release.py --app '/path/to/staging/Multicam Studio.app' \
  --sources-dir /path/to/extracted-source-archive --output-dir /path/to/signed-release \
  --entitlements packaging/entitlements.plist \
  --identity 'Developer ID Application: Your Name (TEAMID)' --team-id TEAMID --arch arm64
```

Use `--arch x86_64 --entitlements packaging/entitlements-intel.plist` for an Intel app.
Use `--package-only` to rebuild installer/source archives from an already signed app;
all component and installation checks still run. The sources directory contains the
`multicam-studio` and `third-party` directories from the matching Sources ZIP.
Remove accidentally collected `.dSYM__` files from the notices in older builds,
and include the real PyObjC license files, before signing those staged copies.
The updated notice collector prevents this issue in new builds.

Signed-only releases can still require macOS's individual Open Anyway approval
for downloaded apps. No notarization or Gatekeeper acceptance is claimed.

## Optional notarization (separate publisher action)

The supplied signed releases have not been submitted to Apple. The commands below
are reference instructions only; `sign_release.py` does not run them.


Without a signing identity, PyInstaller applies an ad-hoc signature. This is not a
Developer ID signature or notarization. It can be tested locally, but downloaded
copies may show Gatekeeper warnings. macOS's Open Anyway flow is for a user who
trusts that specific build; global Gatekeeper changes are not part of installation.

For certificate and Keychain setup, follow [SIGNING-SETUP.md](SIGNING-SETUP.md).

For a public release, provide your own Apple Developer ID Application identity:

```bash
export MULTICAM_CODESIGN_IDENTITY='Developer ID Application: Your Organization (TEAMID)'
build-venv/bin/python packaging/build_release.py --work-dir /path/to/build
xcrun notarytool submit /path/to/release.dmg --keychain-profile YOUR_PROFILE --wait
xcrun stapler staple /path/to/release.dmg
xcrun stapler validate /path/to/release.dmg
spctl --assess --type open --context context:primary-signature --verbose /path/to/release.dmg
```

Use a notarization profile you configured in your own Keychain. No Apple credentials
or signing certificates are supplied by this project. Check the actual notary result
before claiming a package is notarized. Recompute SHA256SUMS after stapling; to ship a
notarized app ZIP, staple the app itself and recreate the ZIP as well. Signing and
notarization are external release steps, not prerequisites for local development.

Official references:
- https://pyinstaller.org/en/stable/spec-files.html
- https://pyinstaller.org/en/stable/usage.html#macos-specific-options
- https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution
- https://www.ffmpeg.org/legal.html

## Runtime entitlements

Apple silicon uses only `com.apple.security.cs.allow-jit` for Python/Objective-C
callbacks. Intel also requires `com.apple.security.cs.allow-unsigned-executable-memory`:
with only allow-jit, the signed Intel runtime stalled in ctypes/libffi
`ffi_closure_alloc` during its self-test. The extra permission is limited to the
Intel main executable; library validation remains enabled. Entitlements are never
applied to libraries. See [PyObjC's signing guidance](https://pyobjc.readthedocs.io/en/latest/notes/codesigning.html).
