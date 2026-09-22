# Multicam Studio

A local macOS editor for multicamera DJ recordings. Sync camera audio to a master bounce, generate a seeded edit, position fixed crops, direct important cuts on a waveform, and export highlights with optional effects.

## Install

[Download the latest release](https://github.com/ZeusyBoy99/multicam-studio/releases/latest). Requires **macOS 14 Sonoma or newer**.

| Your Mac | Installer |
| --- | --- |
| Apple silicon (M1 and later) | `Multicam-Studio-1.1.0-macOS-arm64.dmg` |
| Intel | `Multicam-Studio-1.1.0-macOS-x86_64.dmg` |

Open the DMG, drag **Multicam Studio** into **Applications**, and open it. The setup wizard helps you choose recordings and export folders. Python, NumPy, SciPy, FFmpeg and FFprobe are included. Editing works locally without internet or a Terminal window.

The apps and DMGs are **Developer ID signed, without Apple notarization**. If macOS blocks a trusted downloaded copy, use **System Settings → Privacy & Security → Open Anyway** for that app.

## Make an edit

1. Add the master audio bounce, then add cameras and their recording parts.
2. Choose landscape or portrait output, your main camera, and the cutting rhythm.
3. Set each clip to fit or crop; drag its crop in the preview to choose the fixed framing.
4. Use the audio waveform to place important camera changes. The remaining cuts follow your random seed.
5. Build a preview plan, then render. Use **Highlights** to select clips and **Effects** to style an export.

## Included tools

- Any number of cameras, with independently synchronized recording parts and MOV/MP4 support.
- Audio correlation, printed offsets, manual sync overrides and optional constant drift correction.
- Landscape 3840×2160 or portrait 2160×3840 H.264 output, with the master bounce as the only audio track.
- A selectable main camera, adjustable hold lengths, primary-camera share and random seed.
- Fixed framing for individual clips, with a draggable full-picture crop preview.
- Audio playback, waveform selection and manual camera/part intervals.
- Energy-based highlight suggestions, manual clip export, fades, bounce and visual styles.
- Saved projects, draft recovery, progress, cancellation, render history and setup diagnostics.

Energy suggestions use audio analysis; they do not recognize the DJ's hand movements or guarantee musical drop detection. Camera motion is not added to the main edit; bounce is an optional effect applied afterward.

See the [complete user and command-line guide](docs/USER_GUIDE.md) for controls, examples and syncing details.

## Run from source

Use Python 3.10 or newer and FFmpeg/FFprobe. From this repository's folder:

```sh
brew install ffmpeg
python3 -m venv .venv
.venv/bin/python -m pip install numpy scipy
.venv/bin/python server.py --open
```

The standalone editor is `multicam_edit.py`; run `.venv/bin/python multicam_edit.py --help` for its options. The browser interface runs on a local server. A plain HTML file cannot render video by itself.

## Build the macOS apps

See [release building and signing](packaging/RELEASE.md) and [Developer ID certificate setup](packaging/SIGNING-SETUP.md). Builds are separate for Apple silicon and Intel. The signing helper never submits to Apple for notarization.

Version 1.1.0 passed runtime-component signature checks, real DMG/ZIP installation tests and bundled rendering tests. Native startup was checked on Apple silicon and Intel under Rosetta. Physical Intel hardware and a separate macOS 14 machine were not available for testing.

## Third-party sources

Bundled components retain their own licenses; see [third-party notices](packaging/notices/THIRD-PARTY-NOTICES.txt). Each release includes matching Sources archives with the application, exact FFmpeg/x264 sources and build recipes. Keep the matching Sources archive with the binary package when redistributing it.
