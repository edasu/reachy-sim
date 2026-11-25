# settings.py — Everything you might want to change, in one place.

from pathlib import Path
from reachy_mini.utils import create_head_pose


# ---------------------- Voice (Kokoro) ----------------------

# Kokoro voice: "af_heart", "af_sky", "af_nicole", "af_bella", "bf_lily" (af_ = American, bf_ = British)
VOICE = "af_heart"
PITCH = 1.2  # 1.0 = normal; higher = smaller, cuter voice (try 1.1 – 1.35)
SPEED = 1.0  # Lower = slower, calmer

KOKORO_MODEL = "models/kokoro-v1.0.onnx"  # Downloaded once, see SETUP.md
KOKORO_VOICES = "models/voices-v1.0.bin"
VOICE_CACHE = Path(".voice_cache")  # Saved audio for fixed phrases, so they play instantly


# ---------------------- Brain (Ollama) ----------------------

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


# ---------------------- Body (Reachy) ----------------------

# Pose for each mood tag (antennas are [right, left] in radians)
MOODS = {
    "happy": dict(head=create_head_pose(z=8, pitch=-10, roll=8, mm=True), antennas=[0.6, -0.6]),
    "curious": dict(head=create_head_pose(x=8, pitch=-8, roll=18, mm=True), antennas=[0.3, 0.6]),
    "thinking": dict(head=create_head_pose(pitch=-15, yaw=15, roll=-8, mm=True), antennas=[-0.2, 0.4]),
    "sad": dict(head=create_head_pose(z=-10, pitch=15, mm=True), antennas=[-0.8, 0.8]),
    "excited": dict(head=create_head_pose(z=12, pitch=-12, mm=True), antennas=[0.9, -0.9]),
    "neutral": dict(head=create_head_pose(), antennas=[0.0, 0.0]),
}
# Extra poses used while Reachy listens (not mood tags)
LISTENING = dict(head=create_head_pose(x=6, pitch=-5, roll=10, mm=True), antennas=[0.4, -0.4])  # Leaning in
NOD_DOWN = dict(head=create_head_pose(x=6, pitch=8, roll=10, mm=True), antennas=[0.5, -0.5])  # Half of a nod


# ---------------------- Ears (Whisper + microphone) ----------------------

# How you talk to Reachy: "voice" = speak into the microphone, "text" = type
INPUT_MODE = "voice"
WHISPER_MODEL = "base.en"  # "tiny.en" = faster, "small.en" = more accurate (downloaded on first run)
MIC_RATE = 16000  # Whisper expects 16 kHz audio
SILENCE_SECONDS = 0.8  # How long you must be quiet before Reachy thinks you're done
PATIENCE_SECONDS = 8  # After "hmm" / "let me think", how long Reachy waits for you before answering anyway
MAX_RECORD_SECONDS = 15


# ---------------------- Words ----------------------

WAIT_PHRASE = "Take your time, I'm listening."

# If you end with one of these, you're still thinking, so Reachy waits instead of answering
THINKING_PHRASES = ("let me think", "hold on", "give me a second", "give me a moment", "one second", "one sec", "just a second")
FILLERS = ("hmm", "hm", "mm", "um", "umm", "uh", "uhh", "erm", "er", "well", "wait", "so")  # Only fillers = still thinking
UNFINISHED_ENDINGS = ("and", "but", "so", "because", "or", "the", "a", "an", "my", "if", "um", "uh", "hmm")

GOODBYE_WORDS = ("bye", "goodbye")  # End the chat anywhere in a sentence ("Okay, bye Reachy!")
QUIT_WORDS = ("quit", "exit", "stop", "end", "by")  # End the chat only when said alone ("Stop.")
