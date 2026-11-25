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
| Conductor | `chat.py` + `reachy_chat/` | Connects the four parts above |

---

## Project layout

```
reachy-sim/
├── chat.py              ← start here: the conversation, step by step
├── reachy_chat/         ← the parts chat.py uses
│   ├── settings.py      ← everything you might want to change (voice, personality, poses, timings)
│   ├── words.py         ← understanding what you said: "bye"? "hmm"? unfinished sentence?
│   ├── voice.py         ← Voice class: turns text into speech (Kokoro) and plays it
│   └── ears.py          ← Ears class: records the microphone and turns speech into text (Whisper)
├── models/              ← Kokoro voice files (downloaded in step 4, not in git)
├── .voice_cache/        ← saved audio for fixed phrases (made automatically, not in git)
├── hello.py, talk.py    ← simple older demos
└── movement.md          ← reference for head poses and expressions
```

The brain (Ollama) and body (robot moves) code is still inside `chat.py`.

---

## Requirements

- macOS (`hello.py` and `talk.py` use the built-in `say` command, and the voice test uses `afplay`)
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
- `faster-whisper`: speech-to-text (Reachy's ears)
- `sounddevice`: records the microphone and plays Reachy's voice

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

> You can use a different model (e.g. `qwen2.5`, `gemma3`). Pull it with `ollama pull <name>` and change `MODEL` in `reachy_chat/settings.py`.
>
> Reachy's personality is `SYSTEM_PROMPT` in the same file.

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

In `reachy_chat/settings.py`:

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
>
> After changing the voice, the saved phrases in `.voice_cache/` are made again automatically.

### Talk with your voice (Whisper)

Reachy hears you through your microphone. Your speech is turned into text on your computer by `faster-whisper`, which step 2 installs, so nothing is sent online.

- Download the Whisper model (`base.en`, about 150 MB) once, so it works offline afterwards:

  ```bash
  .venv/bin/python -c "from faster_whisper import WhisperModel; WhisperModel('base.en')"
  ```

  (If you skip this, `chat.py` downloads it on its first run.)
- The first time, macOS asks whether your terminal or VS Code may use the microphone. Click **Allow**. If you clicked "Don't Allow", turn it on in **System Settings → Privacy & Security → Microphone**.

- Whisper runs on the Mac's GPU when it can (about 0.2 s per sentence), and falls back to the CPU otherwise.

Settings in `reachy_chat/settings.py`:

```python
INPUT_MODE = "voice"       # "voice" = speak, "text" = type
WHISPER_MODEL = "base.en"  # "tiny.en" = faster, "small.en" = more accurate
SILENCE_SECONDS = 0.8      # How long you stay quiet before Reachy answers
PATIENCE_SECONDS = 8       # After "hmm" / "let me think", how long Reachy waits before answering anyway
```

### Reachy waits while you think

Reachy doesn't answer if you're clearly not finished:

| You say | Reachy |
|---|---|
| "Hmm.", "Um...", "Wait.", "Let me think." | Says *"Take your time, I'm listening."*, nods, keeps listening |
| "…pizza and", "Because", "So I was thinking about..." | Nods and keeps listening |
| A finished sentence, or anything ending in "?" or "!" | Answers right away |

If you stay quiet for `PATIENCE_SECONDS` after a "hmm", Reachy answers what you said so far. The word lists (`THINKING_PHRASES`, `FILLERS`, `UNFINISHED_ENDINGS`) are in `reachy_chat/settings.py`.

## 5. Start the simulator

Open a **separate terminal window** and keep it running:

```bash
.venv/bin/mjpython -m reachy_mini.daemon.app.main --sim
```

On macOS, the 3D simulator window needs `mjpython` (MuJoCo's Python launcher) instead of plain `python`. A window with Reachy Mini should open.

> No window needed? `.venv/bin/reachy-mini-daemon --sim --headless` runs the simulator without graphics.

## 6. Run Reachy

In your main terminal, **from the project folder** (so `chat.py` can find `reachy_chat/` and `models/`):

```bash
.venv/bin/python chat.py
```

1. It prints `Loading Reachy's voice...` and `Loading Reachy's ears...`. The very first start takes about 30 s while it warms up and saves phrases to `.voice_cache/`; later starts are faster.
2. Stay quiet while it prints `Measuring room noise...`.
3. Reachy says hi and moves.
4. When you see `(listening... talk now)`, speak. Reachy answers about a second after you stop talking, and moves to match the mood while it talks. Say **bye** to stop (or just "stop" on its own).
   (With `INPUT_MODE = "text"`, type instead.)

After each answer, a timing line shows where the waiting time went:

```
[timing] understand 0.16s | brain 0.18s | voice 0.47s | Reachy started talking 0.81s after you stopped (+0.8s pause to be sure you were done)
```

| Part | Meaning |
|---|---|
| understand | Whisper turning your speech into text |
| brain | Ollama writing the first sentence |
| voice | Kokoro making each sentence, in order |
| started talking | The total delay you notice (after the `SILENCE_SECONDS` pause) |

---

## Other scripts

| File | What it does |
|---|---|
| `hello.py` | Says "Hello! How are you?" with simple head and antenna moves (Mac `say` voice) |
| `talk.py` | A short scripted conversation (Mac `say` voice) |
| `chat.py` | Free spoken AI conversation: Whisper ears + Ollama brain + Kokoro voice + mood-based moves (uses `reachy_chat/`) |
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
| `ModuleNotFoundError: reachy_chat` | Script run from another folder | `cd` into the project folder first |
| "The microphone gives only silence, so macOS is probably blocking it." | No microphone permission | System Settings → Privacy & Security → Microphone → turn on VS Code (or Terminal), then fully quit and reopen it |
| Reachy is slow to answer | Look at the `[timing]` line to see which part is slow | **voice** slow: the simulator window uses a lot of CPU, so try `--headless`. **understand** slow: try `WHISPER_MODEL = "tiny.en"`. **brain** slow: try a smaller Ollama model |
| Reachy never reacts when you talk, or `You:` is empty | You're too quiet, or the room was loud during the noise check | Speak a little closer, and restart in a quiet moment |
| Reachy answers before you finish | You pause longer than `SILENCE_SECONDS` | Raise `SILENCE_SECONDS` to 1.2 |
| Reachy waits a long time before answering | Your sentence ended like an unfinished one ("…and", "hmm") | Finish the sentence, or lower `PATIENCE_SECONDS` |
| Reachy keeps "hearing" noise | Noisy room | Run the noise check in silence, or use `INPUT_MODE = "text"` |
| Warning messages when the voice or ears load | Normal library messages | Safe to ignore |
