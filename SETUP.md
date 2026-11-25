# Setup Guide

How to set up this project from scratch on a Mac, so Reachy Mini can move in the simulator, think with a local AI (Ollama), hear you through the microphone (Whisper), and talk with a natural voice (Kokoro).

Everything runs **on your own computer**. No account, API key, or internet connection is needed after setup.

---

## What you'll set up

| Part | Tool | Role |
|---|---|---|
| Body | Reachy Mini daemon + MuJoCo simulator | Moves the robot's head, antennas and body |
| Brain | Ollama + `llama3.2` | Writes Reachy's replies |
| Ears | Whisper (`faster-whisper`) + microphone | Turns what you say into text |
| Voice | Kokoro (`kokoro-onnx`) | Turns Reachy's replies into speech |
| Conductor | `chat.py` | Connects the four parts above |

---

## Requirements

- macOS (the scripts use the built-in `afplay` and `say` commands)
- A microphone (the Mac's built-in one is fine)
- [Homebrew](https://brew.sh)
- About **3 GB** of free disk space (≈2 GB for the AI model, ≈340 MB for the voice, ≈150 MB for the ears)

---

## 1. Install `uv` (Python project manager)

```bash
brew install uv
```

`uv` installs the right Python version (3.13, see `.python-version`) and all the libraries for you.

## 2. Install the project's libraries

From the project folder:

```bash
uv sync
```

This reads `pyproject.toml` and installs everything into a `.venv` folder, including:
- `reachy-mini[mujoco]`: the robot library and simulator
- `kokoro-onnx`: the voice engine

## 3. Set up the brain (Ollama)

Install Ollama and download the AI model (about 2 GB):

```bash
brew install ollama
brew services start ollama   # keeps Ollama running in the background
ollama pull llama3.2
```

Check it worked:

```bash
ollama list   # should show llama3.2
```

> You can use a different model (e.g. `qwen2.5`, `gemma3`). Pull it with `ollama pull <name>` and change `MODEL` in `chat.py`.

## 4. Set up the voice (Kokoro)

The `kokoro-onnx` library is already installed by step 2, but it needs two model files. Download them into a `models/` folder:

```bash
mkdir -p models
cd models
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
cd ..
```

| File | Size | What it is |
|---|---|---|
| `kokoro-v1.0.onnx` | 310 MB | The voice AI model |
| `voices-v1.0.bin` | 27 MB | All the different voices |

The `models/` folder is in `.gitignore` because these files are too big for git. **Everyone who clones the project needs to download them once.**

### Test the voice

```bash
.venv/bin/python -c "
from kokoro_onnx import Kokoro
import wave, subprocess, numpy as np
k = Kokoro('models/kokoro-v1.0.onnx', 'models/voices-v1.0.bin')
samples, sr = k.create('Hi! I am Reachy.', voice='af_heart', lang='en-us')
with wave.open('test.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((np.clip(samples, -1, 1) * 32767).astype(np.int16).tobytes())
subprocess.run(['afplay', 'test.wav'])
"
rm test.wav
```

You should hear "Hi! I am Reachy."

### Change the voice

At the top of `chat.py`:

```python
VOICE = "af_heart"  # Which voice
PITCH = 1.2         # 1.0 = normal; higher = smaller, cuter robot voice (try 1.1 – 1.35)
SPEED = 1.0         # Lower = slower, calmer
```

Cute/warm voices to try: `af_heart`, `af_bella`, `af_nicole`, `af_sky`, `bf_lily`.
`af_` = American female, `bf_` = British female. To see every voice:

```bash
.venv/bin/python -c "from kokoro_onnx import Kokoro; print(Kokoro('models/kokoro-v1.0.onnx', 'models/voices-v1.0.bin').get_voices())"
```

> British voices (`bf_...`) automatically use British pronunciation.

### Talk with your voice (Whisper)

Reachy hears you through your microphone. Your speech is turned into text on your computer by `faster-whisper`, which step 2 installs, so nothing is sent online.

- Download the Whisper model (`base.en`, about 150 MB) once, so it works offline afterwards:

  ```bash
  .venv/bin/python -c "from faster_whisper import WhisperModel; WhisperModel('base.en')"
  ```

  (If you skip this, `chat.py` downloads it on its first run.)
- The first time, macOS asks whether your terminal or VS Code may use the microphone. Click **Allow**. If you clicked "Don't Allow", turn it on in **System Settings → Privacy & Security → Microphone**.

Settings at the top of `chat.py`:

```python
INPUT_MODE = "voice"       # "voice" = speak, "text" = type
WHISPER_MODEL = "base.en"  # "tiny.en" = faster, "small.en" = more accurate
SILENCE_SECONDS = 1.0      # How long you stay quiet before Reachy answers
```

## 5. Start the simulator

Open a **separate terminal window** and keep it running:

```bash
.venv/bin/mjpython -m reachy_mini.daemon.app.main --sim
```

On macOS, the 3D simulator window needs `mjpython` (MuJoCo's Python launcher) instead of plain `python`. A window with Reachy Mini should open.

> No window needed? `.venv/bin/reachy-mini-daemon --sim --headless` runs the simulator without graphics.

## 6. Run Reachy

In your main terminal:

```bash
.venv/bin/python chat.py
```

1. It prints `Loading Reachy's voice...` and `Loading Reachy's ears...` (takes a few seconds).
2. Stay quiet while it prints `Measuring room noise...`.
3. Reachy says hi and moves.
4. When you see `(listening... talk now)`, speak. Reachy answers once you stop talking. Say **bye** to stop (or just "stop" on its own).
   (With `INPUT_MODE = "text"`, type instead.)

---

## Other scripts

| File | What it does |
|---|---|
| `hello.py` | Says "Hello! How are you?" with simple head and antenna moves (Mac `say` voice) |
| `talk.py` | A short scripted conversation (Mac `say` voice) |
| `chat.py` | Free spoken AI conversation: Whisper ears + Ollama brain + Kokoro voice + mood-based moves |
| `movement.md` | Reference for head poses, antennas and ready-made expressions |

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `Ollama error: model 'llama3.2' not found` | The AI model isn't downloaded | `ollama pull llama3.2` |
| "I can't reach my brain. Is Ollama running?" | Ollama isn't running | `brew services start ollama` (or open the Ollama app) |
| `No such file ... kokoro-v1.0.onnx` | Voice files missing, or script run from another folder | Do step 4, and run scripts from the project folder |
| Script can't connect to the robot | Simulator isn't running | Do step 5 in a separate terminal first |
| `ModuleNotFoundError: reachy_mini` / `kokoro_onnx` | Using the system Python instead of the project's | Run with `.venv/bin/python` (or `uv run python`) |
| Long pause before Reachy answers | The AI model is generating | Normal for the first message; a smaller model is faster |
| Reachy never reacts when you talk, or `You:` is empty | No microphone permission, or you're too quiet | Allow the mic in System Settings → Privacy & Security → Microphone, and speak a little closer |
| Reachy answers before you finish | Pauses longer than `SILENCE_SECONDS` | Raise `SILENCE_SECONDS` to 1.5 |
| Reachy keeps "hearing" noise | Noisy room | Run the noise check in silence, or use `INPUT_MODE = "text"` |
| A few warning messages when the voice loads | Normal Kokoro/phonemizer messages | Safe to ignore |
