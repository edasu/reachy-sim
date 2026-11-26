# Reachy Sim

Talk out loud with a simulated **Reachy Mini** robot. It listens, thinks, answers in a natural voice, and moves its head and antennas to match the mood.

Everything runs **locally on your Mac**. You don't need an account or an API key.

| Part | Tool |
|---|---|
| Body | Reachy Mini daemon + MuJoCo simulator |
| Brain | Ollama + `llama3.2` (3B) |
| Ears | Whisper (`faster-whisper`) |
| Voice | Kokoro (`kokoro-onnx`) |

## Quick start

```bash
brew install uv ollama
uv sync
brew services start ollama && ollama pull llama3.2

mkdir -p models && cd models
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
cd ..
```

Then use two terminals:

```bash
.venv/bin/mjpython sim.py   # 1. start the simulator
.venv/bin/python chat.py    # 2. talk to Reachy (say "bye" to stop)
```

## Project layout

```
chat.py          main conversation loop (start here)
reachy_chat/     settings, ears, voice, body, and word helpers
sim.py           starts the simulator
hello.py, talk.py  simple scripted demos
movement.md      head pose and expression reference
```

## Customize

All the knobs are in [`reachy_chat/settings.py`](reachy_chat/settings.py): the AI model (`MODEL`), voice, personality, poses, timings, and text or voice input (`INPUT_MODE`).

## More

For full setup, tuning, and troubleshooting, see [SETUP.md](SETUP.md).
