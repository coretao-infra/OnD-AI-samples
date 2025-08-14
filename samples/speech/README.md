# 🎙️ On-Device AI Lab: Live Captions (Whisper + Rich UI)

**Transform your Windows PC into a powerful offline “Live Captions” tool with a professional terminal interface.**

This app demonstrates real-time speech transcription using OpenAI Whisper models with voice activity detection, featuring a sophisticated Rich-based terminal UI.

---

## ✨ Current Features

- **Real-time audio capture** (16kHz mono, selectable input device)
- **Voice Activity Detection** (WebRTC VAD for smart utterance segmentation)
- **OpenAI Whisper integration** (tiny/base/small models, fully local)
- **Live VU meters** (stereo, color-coded, real-time)
- **Rich terminal UI** (XTree-style, multi-panel, responsive)
- **Transcription log** (scrolling, timestamped)
- **Device selection panel** (visual, with status markers)
- **Controls panel** (hotkey reference, status display)
- **Async architecture** (non-blocking, robust error handling)

---

## 📝 TODO / Roadmap

### 🖥️ User Experience & Hotkeys
- [ ] Implement all hotkeys shown in the UI:
  - [ ] `SPACE`: Start/Stop capture (currently only programmatic start)
  - [ ] `ESC`: Exit application cleanly
  - [ ] `F1`: Show/hide hotkeys overlay
  - [ ] `F2`: Save transcript to file
  - [ ] `F3`: Load file to transcribe
  - [ ] `F4`: New transcript (clear log)
  - [ ] `F5`: Toggle system audio (Stereo Mix)
  - [ ] `F6`: Select input device interactively
- [ ] Add keyboard navigation for device selection
- [ ] Add confirmation dialogs for file operations
- [ ] Status box should display the last detected language
- [ ] VU meter should show real-time audio processing info (e.g., queue length, last audio message length, chunk window size) instead of stereo bars, since most audio is mono

### 🏗️ Architecture & Code Quality
- [ ] Refactor for testability without breaking real-time performance
- [ ] Modularize UI and audio logic (carefully, to avoid regressions)
- [ ] Add unit/integration tests for audio and VAD pipeline
- [ ] Improve error handling for device selection and audio failures
- [ ] Support for background/daemon mode

### 🧠 Features & Enhancements
- [ ] Streaming partial transcription (word-by-word, not just utterance)
- [ ] Overlay GUI window (Tkinter or PySimpleGUI)
- [ ] Output to file/clipboard
- [ ] Multi-language auto-detection
- [ ] GPU support (CUDA, if available)
- [ ] Configurable VAD aggressiveness
- [ ] Customizable UI themes

---


# Prerequisites

- Windows 10/11
- Python 3.12+ from python.org (includes Tkinter on Windows)
- A working microphone (or "Stereo Mix" enabled for system audio - see Settings > Sound > Sound Control Panel > Recording tab to enable)
- Fully local inference: no cloud calls.
- Simple to set up: minimal dependencies, small "tiny/base" models to start.
- Fast response: expect 1-3 second processing delays with recommended models.

This lab turns your Windows PC into an offline “Live Captions” tool. It listens to your microphone, detects speech locally, and shows real-time captions using Whisper models. Everything runs on-device; after the first model download, it works offline.

Why this is a good lab
- Practical: live transcription for meetings, calls, and videos played through speakers (with stereo mix).
- Fully local inference: no cloud calls.
- Simple to set up: minimal dependencies, small “tiny/base” models to start.

What you build:
- A minimal app that:
  - Captures mic audio (or system audio with stereo mix enabled)
  - Uses VAD (voice activity detection) to segment speech
  - Streams transcriptions from a Whisper model (tiny/base/small)
  - Shows real-time captions in a console or a small GUI window

Notes:
- The recommended path is CPU with the tiny or base models for responsiveness.
- GPU acceleration is optional and mainly for NVIDIA CUDA setups (see below).
- First run downloads the model (may take a moment) - after that, it's fully offline.

## Prerequisites

- Windows 10/11
- Python 3.9–3.12 from python.org (includes Tkinter on Windows)
- A working microphone (or “Stereo Mix” enabled if captioning system audio)

## Setup

```powershell
# 1) Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# 2) Install dependencies
# - faster-whisper: Whisper inference via CTranslate2 (lightweight for CPU)
# - sounddevice: mic capture (PortAudio)
# - webrtcvad: robust VAD
# - rich: nicer console output (optional but helpful)
# Note: First run will download model weights (~40MB for tiny, ~140MB for base)
pip install faster-whisper sounddevice webrtcvad numpy rich
```

Optional GPU (NVIDIA CUDA):
- If you have an NVIDIA GPU with a supported CUDA runtime and drivers, you can try `device=cuda` with faster-whisper.
- On Windows this requires a CUDA-enabled CTranslate2 build. If the default wheel lacks CUDA support, consult CTranslate2/faster-whisper docs for GPU wheel installation. 
- Otherwise, keep using CPU (recommended for simplicity and compatibility).

## Run

If your sample includes a GUI:
```powershell
python app.py
```

Console-only example (typical flags your app can support):
```powershell
python app.py --model-size tiny --language en --device cpu --compute-type int8
```

Suggested flags (implement as appropriate in your app.py):
- `--model-size`: tiny | base | small (tiny is fastest; small is better quality but slower)
- `--language`: ISO code (e.g., en, es, fr). If omitted, model attempts to detect.
- `--device`: cpu (default). Use cuda only if you have CUDA set up.
- `--compute-type`: int8 | int8_float16 | float16 | float32 (int8 is fastest on CPU).
- `--mic-index`: choose the input device if multiple mics exist.
- `--vad`: webrtc (recommended), or disable to stream raw audio (more latency and errors).

List your audio devices:
```powershell
python -c "import sounddevice as sd; print(sd.query_devices())"
```

## How it works

- Audio capture: sounddevice collects 16 kHz mono audio frames.
- VAD: webrtcvad detects speech vs. silence to form utterances.
- Transcription: faster-whisper loads a Whisper model and transcribes chunks locally.
- Streaming: partial results can be shown as words arrive; final text replaces the partial line at segment end.

## Model tips

- Start with: tiny (fastest) or base (balanced).
- If you need better accuracy and can tolerate latency, try small.
- First run downloads the model weights to your local cache. After that, it’s fully offline.

## Troubleshooting

- No device found: run the device listing command above to find the correct mic.
- Permissions: ensure microphone access is allowed in Windows Settings.
- Clipping/low volume: adjust your mic level or use a headset mic.
- Latency: use tiny model and int8 compute type; ensure you’re not running in a throttled environment.
- GPU not used: keep using CPU unless you’ve explicitly installed a CUDA-enabled CTranslate2 build.

## Next steps

- Add hotkeys (e.g., start/stop) with `pynput`.
- Output to a text file or copy to clipboard.
- Add a small Tkinter overlay window with always-on-top captions.