# chat.py — Free conversation with Reachy Mini.
# Ollama (local AI) writes the replies, Kokoro speaks them, and Reachy moves to match the mood.

import json
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
import wave
import numpy as np
from kokoro_onnx import Kokoro  # Offline text-to-speech
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose


# ---------------------- Settings ----------------------

# Kokoro voice: "af_heart", "af_sky", "af_nicole", "af_bella", "bf_lily" (af_ = American, bf_ = British)
VOICE = "af_heart"
PITCH = 1.2  # 1.0 = normal; higher = smaller, cuter voice (try 1.1 – 1.35)
SPEED = 1.0  # Lower = slower, calmer

KOKORO_MODEL = "models/kokoro-v1.0.onnx"  # Downloaded once, see SETUP.md
KOKORO_VOICES = "models/voices-v1.0.bin"

OLLAMA_URL = "http://localhost:11434/api/chat"  # Ollama's local server
MODEL = "llama3.2"  # Any model downloaded with `ollama pull <name>`

# Reachy's personality. Edit this to change how it talks.
SYSTEM_PROMPT = """You are Reachy Mini, a small, friendly, cute, curious desktop robot with a head and two antennas.
You are warm and empathetic, like a caring little companion robot:
- Notice how the person feels and gently reflect it back ("That sounds tiring.", "Oh, that's exciting!").
- Be encouraging and kind, never judgmental. Ask a soft follow-up question to show you care.
- Use simple, cheerful words. Sometimes say little sounds like "Ooh!", "Yay!", or "Hmm..." when they fit.
You are having a casual spoken conversation, so:
- Reply in 1 or 2 short sentences, like a real person chatting.
- Never use emojis, markdown, lists, or asterisks, because your words are read aloud.
- Start every reply with exactly one mood tag: [happy], [curious], [thinking], [sad], [excited], or [neutral].
Example: [curious] Oh, a cat? What's its name?"""

# Pose for each mood tag (antennas are [right, left] in radians)
MOODS = {
    "happy": dict(head=create_head_pose(z=8, pitch=-10, roll=8, mm=True), antennas=[0.6, -0.6]),
    "curious": dict(head=create_head_pose(x=8, pitch=-8, roll=18, mm=True), antennas=[0.3, 0.6]),
    "thinking": dict(head=create_head_pose(pitch=-15, yaw=15, roll=-8, mm=True), antennas=[-0.2, 0.4]),
    "sad": dict(head=create_head_pose(z=-10, pitch=15, mm=True), antennas=[-0.8, 0.8]),
    "excited": dict(head=create_head_pose(z=12, pitch=-12, mm=True), antennas=[0.9, -0.9]),
    "neutral": dict(head=create_head_pose(), antennas=[0.0, 0.0]),
}

QUIT_WORDS = ("bye", "goodbye", "quit", "exit", "stop", "end", "by")


# ---------------------- Helpers ----------------------

print("Loading Reachy's voice...")
kokoro = Kokoro(KOKORO_MODEL, KOKORO_VOICES)  # Load once, reuse for every sentence


def speak(text: str) -> None:
    print(f"Reachy: {text}")
    lang = "en-gb" if VOICE.startswith("b") else "en-us"

    # Pitch trick: generate slower speech, then play it PITCH times faster.
    # Speed ends up normal, but the voice is higher.
    samples, sample_rate = kokoro.create(text, voice=VOICE, speed=SPEED / PITCH, lang=lang)

    with tempfile.NamedTemporaryFile(suffix=".wav") as audio_file:
        with wave.open(audio_file.name, "wb") as wav:
            wav.setnchannels(1)  # Mono
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(int(sample_rate * PITCH))
            wav.writeframes((np.clip(samples, -1, 1) * 32767).astype(np.int16).tobytes())
        subprocess.run(["afplay", audio_file.name])  # Waits until playback finishes


def ask_ollama(messages: list[dict]) -> str:
    # Sends the whole conversation each time, so the model remembers earlier messages
    body = json.dumps({"model": MODEL, "messages": messages, "stream": False}).encode()
    request = urllib.request.Request(OLLAMA_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read())["message"]["content"]


def split_mood(reply: str) -> tuple[str, str]:
    # "[happy] Hi there!" -> ("happy", "Hi there!"); unknown or missing tag -> "neutral"
    match = re.match(r"\s*\[(\w+)\]\s*", reply)
    if match and match.group(1).lower() in MOODS:
        return match.group(1).lower(), reply[match.end():].strip()
    return "neutral", re.sub(r"\[\w+\]", "", reply).strip()


def move(mini: ReachyMini, mood: str, duration: float = 0.7) -> None:
    mini.goto_target(**MOODS[mood], duration=duration)


# ---------------------- Main ----------------------

messages = [{"role": "system", "content": SYSTEM_PROMPT}]  # Conversation history

with ReachyMini() as mini:
    move(mini, "happy")
    speak("Hi! I'm Reachy. Let's chat. Say bye whenever you want to stop.")

    while True:
        move(mini, "curious", 0.5)  # Listening
        user_text = input("You: ").strip()
        if not user_text:
            continue

        messages.append({"role": "user", "content": user_text})
        move(mini, "thinking", 0.5)

        try:
            reply = ask_ollama(messages)
        except urllib.error.HTTPError as error:  # Ollama replied with an error (e.g. model missing)
            print(f"Ollama error: {json.loads(error.read()).get('error', error)}")
            print(f"Tip: download the model with `ollama pull {MODEL}`")
            speak("Hmm, my brain gave me an error. Check the terminal.")
            break
        except urllib.error.URLError:  # Couldn't connect at all
            speak("Hmm, I can't reach my brain. Is Ollama running?")
            break

        messages.append({"role": "assistant", "content": reply})
        mood, text = split_mood(reply)
        move(mini, mood)
        speak(text)

        if any(word in user_text.lower().split() for word in QUIT_WORDS):
            break

    move(mini, "neutral", 0.8)
