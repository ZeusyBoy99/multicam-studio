#!/usr/bin/env python3
"""Sign and package an existing Multicam Studio app. Never submits to notarization.

Operate on a fresh, verified app copy on APFS, not the installed/running app.
Requires a Developer ID Application identity in the local Keychain.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import struct
import subprocess
import tempfile
import zipfile


def run(args, capture=False, env=None, timeout=None):
    p = subprocess.run([str(x) for x in args], capture_output=True, text=True, env=env, timeout=timeout)
    if p.returncode:
        raise RuntimeError(f"Command failed ({p.returncode}): {args[0]}\n{p.stdout}\n{p.stderr}")
    return (p.stdout + p.stderr).strip()


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def macho_kind(path):
    with path.open('rb') as stream:
        header = stream.read(16)
    if header[:4] == b'\xcf\xfa\xed\xfe':
        return struct.unpack('<I', header[12:16])[0]
    if header[:4] == b'\xfe\xed\xfa\xcf':
        return struct.unpack('>I', header[12:16])[0]
    if header[:4] in (b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca'):
        raise RuntimeError(f'Unexpected universal binary in architecture-specific app: {path}')
    return None


def signature(path, team, runtime=False):
    run(['/usr/bin/codesign', '--verify', '--strict', path])
    detail = run(['/usr/bin/codesign', '--display', '--verbose=4', path])
    if f'TeamIdentifier={team}' not in detail or 'Authority=Developer ID Application:' not in detail:
        raise RuntimeError(f'Unexpected signing identity: {path}\n{detail}')
    if 'Timestamp=' not in detail:
        raise RuntimeError(f'Missing secure signing timestamp: {path}')
    if runtime and '(runtime)' not in detail:
        raise RuntimeError(f'Hardened runtime missing: {path}')
    return detail


def verify_app(app, args):
    run(['/usr/bin/codesign', '--verify', '--deep', '--strict', app])
    detail = signature(app, args.team_id, runtime=True)
    info = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
    if info.get('CFBundleVersion') != info.get('CFBundleShortVersionString'):
        raise RuntimeError('Unexpected bundle version')
    css = (app / 'Contents/Resources/web/studio.css').read_text()
    assert 'position:sticky;top:0;z-index:5' in css and '.studio-tabs{top:0;' in css
    count = 0
    for path in app.rglob('*'):
        if any(part.startswith('._') for part in path.relative_to(app).parts):
            raise RuntimeError(f'AppleDouble metadata in app: {path}')
        if path.is_symlink() or not path.is_file():
            continue
        kind = macho_kind(path)
        if kind is None:
            continue
        if kind not in (2, 6, 8):
            raise RuntimeError(f'Unexpected Mach-O object: {path}')
        signature(path, args.team_id, runtime=(kind == 2))
        architecture = run(['/usr/bin/lipo', '-archs', path]).strip()
        if architecture != args.arch:
            raise RuntimeError(f'Wrong architecture {architecture}: {path}')
        count += 1
    command = [app / 'Contents/MacOS/MulticamStudio', '--self-test']
    if args.arch == 'x86_64':
        command = ['/usr/bin/arch', '-x86_64', *command]
    result = run(command, env=dict(os.environ, PATH='/usr/bin:/bin:/usr/sbin:/sbin'), timeout=120)
    runtime_test = json.loads(result.splitlines()[-1])
    if runtime_test.get('status') != 'ok':
        raise RuntimeError(result)
    return {'macho_files': count, 'team_id': args.team_id, 'runtime_self_test': runtime_test,
            'architecture': args.arch, 'signature': detail}


def make_sources(source_dir, destination):
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(source_dir.rglob('*')):
            relative = path.relative_to(source_dir)
            if any(part.startswith('._') or part == '__pycache__' for part in relative.parts):
                continue
            if path.is_file():
                archive.write(path, str(relative))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', required=True, type=Path)
    parser.add_argument('--sources-dir', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--entitlements', required=True, type=Path)
    parser.add_argument('--identity', required=True)
    parser.add_argument('--team-id', required=True)
    parser.add_argument('--arch', choices=['arm64', 'x86_64'], required=True)
    parser.add_argument('--package-only', action='store_true', help='Verify and package an already Developer ID signed app without re-signing its components')
    args = parser.parse_args()
    app = args.app.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    info = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
    version = info['CFBundleShortVersionString']
    bundle_id = info['CFBundleIdentifier']
    main_executable = app / 'Contents/MacOS' / info['CFBundleExecutable']
    base = ['/usr/bin/codesign', '--force', '--sign', args.identity, '--timestamp']
    if not args.package_only:
        binaries = []
        for path in app.rglob('*'):
            if path.is_symlink() or not path.is_file():
                continue
            kind = macho_kind(path)
            if kind is not None:
                if kind not in (2, 6, 8):
                    raise RuntimeError(f'Remove non-runtime Mach-O data before signing: {path}')
                binaries.append((path, kind))
        for index, (path, kind) in enumerate(sorted(binaries, key=lambda x: (-len(x[0].parts), str(x[0]))), 1):
            if path == main_executable:
                continue
            options = ['--options', 'runtime', '--identifier', bundle_id + '.' + path.name] if kind == 2 else []
            run([*base, *options, path])
            if index % 25 == 0:
                print(f'Signed {index}/{len(binaries)} runtime components', flush=True)
        frameworks = [p for p in app.rglob('*.framework') if p.is_dir() and not p.is_symlink()]
        for framework in sorted(frameworks, key=lambda p: -len(p.parts)):
            run([*base, framework])
        run([*base, '--options', 'runtime', '--entitlements', args.entitlements, app])
    print('App signed. Checking runtime components and rendering.', flush=True)
    verified = verify_app(app, args)
    stem = f'Multicam-Studio-{version}-macOS-{args.arch}'
    sources = args.output_dir / f'Multicam-Studio-{version}-Sources.zip'
    make_sources(args.sources_dir, sources)
    archive = args.output_dir / (stem + '.zip')
    run(['/usr/bin/ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', app, archive])
    install_text = f'''Multicam Studio {version}\n\n1. Drag Multicam Studio.app into Applications.\n2. Open Multicam Studio from Applications.\n3. Choose your recordings and export folders in the setup wizard.\n\nThis package is for {'Apple silicon (M1 and later)' if args.arch == 'arm64' else 'Intel Macs'}.\nRequires macOS 14 Sonoma or newer. Python, NumPy, SciPy, FFmpeg and FFprobe\nare included. Editing does not require Terminal, Homebrew or internet.\n\nThe app is signed with Developer ID Application. It has not been submitted\nto Apple for notarization. macOS may require you to use System Settings >\nPrivacy & Security > Open Anyway on its first launch.\n\nUse Settings or the app menu to quit, after finishing or cancelling renders.\nYour recordings and exports remain in the folders you select.\nSettings and jobs: ~/Library/Application Support/Multicam Studio\nLogs: ~/Library/Logs/Multicam Studio/desktop.log\n\nThe Sources ZIP includes application source, third-party sources, license\nnotices and build instructions. Keep it alongside the binary distribution.\n'''
    with tempfile.TemporaryDirectory(prefix='package-', dir=app.parent) as temp:
        temp = Path(temp)
        staging = temp / 'dmg-content'
        staging.mkdir()
        run(['/usr/bin/ditto', app, staging / 'Multicam Studio.app'])
        run(['/usr/bin/codesign', '--verify', '--deep', '--strict', staging / 'Multicam Studio.app'])
        (staging / 'Applications').symlink_to('/Applications')
        shutil.copy2(sources, staging / sources.name)
        (staging / 'Install Multicam Studio.txt').write_text(install_text)
        dmg = args.output_dir / (stem + '.dmg')
        run(['/usr/bin/hdiutil', 'create', '-volname', 'Multicam Studio', '-srcfolder', staging, '-ov', '-format', 'UDZO', dmg])
        run([*base, dmg])
        signature(dmg, args.team_id)
        mountpoint = temp / 'mounted'
        mountpoint.mkdir()
        run(['/usr/bin/hdiutil', 'attach', '-readonly', '-nobrowse', '-mountpoint', mountpoint, dmg])
        try:
            installed = temp / 'dmg-install' / 'Multicam Studio.app'
            run(['/usr/bin/ditto', mountpoint / 'Multicam Studio.app', installed])
            dmg_check = verify_app(installed, args)
        finally:
            run(['/usr/bin/hdiutil', 'detach', mountpoint])
        zip_destination = temp / 'zip-install'
        run(['/usr/bin/ditto', '-x', '-k', archive, zip_destination])
        zip_check = verify_app(zip_destination / 'Multicam Studio.app', args)
    report = {'version': version, 'architecture': args.arch, 'supported_macos': '14.0+',
              'signing': 'Developer ID Application', 'team_id': args.team_id,
              'notarized': False, 'submitted_to_apple': False,
              'app': verified, 'dmg_installation': dmg_check, 'zip_installation': zip_check}
    (args.output_dir / (stem + '-verification.json')).write_text(json.dumps(report, indent=2) + '\n')
    (args.output_dir / 'Install Multicam Studio.txt').write_text(install_text)
    artifacts = sorted(p for p in args.output_dir.iterdir() if p.is_file() and not p.name.startswith('._') and p.suffix in ('.zip', '.dmg'))
    (args.output_dir / 'SHA256SUMS.txt').write_text(''.join(f'{digest(p)}  {p.name}\n' for p in artifacts))
    print(f'PASS: signed app, signed DMG, both installation tests. Output: {args.output_dir}', flush=True)


if __name__ == '__main__':
    main()
