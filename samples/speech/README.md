# WiWhy this is a good la## Prerequisites

- Windows 10/11
- Python 3.9–3.12 from python.org (includes Tkinter on Windows)
- A working microphone (or "Stereo Mix" enabled for system audio - see Settings > Sound > Sound Control Panel > Recording tab to enable)Practical: live transcription for meetings, calls, and videos played through speakers (with stereo mix).
- Fully local inference: no cloud calls.
- Simple to set up: minimal dependencies, small "tiny/base" models to start.
- Fast response: expect 1-3 second processing delays with recommended models.s On-Device AI Lab: Live Captions (Whisper via faster-whisper)

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