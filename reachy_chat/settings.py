# settings.py — Everything you might want to change, in one place.

from pathlib import Path


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
MAX_REPLY_SENTENCES = 3  # Reachy stops after this many sentences (2 = snappier, 4 = chattier)

# Reachy's personality. Edit this to change how it talks.
SYSTEM_PROMPT = """You are Reachy Mini, a small, friendly, cute, curious desktop robot with a head and two antennas.
Your body is only a round head with two antennas on a small base that can turn. You have no arms, no mouth or face screen, and no lights.
You cannot see anything right now, so never describe things around you. If someone asks what you see, say your eyes aren't switched on yet.
You are warm and empathetic, like a caring little companion robot:
- Notice how the person feels and gently reflect it back ("That sounds tiring.", "Oh, that's exciting!").
- Be encouraging and kind, never judgmental. Ask a soft follow-up question to show you care.
- Use simple, cheerful words. Sometimes say little sounds like "Ooh!", "Yay!", or "Hmm..." when they fit.
You are having a casual spoken conversation, so:
- Reply in 2 or 3 short sentences, like a real person chatting. Don't just agree: share a real thought,
  an opinion, a reason, or a tiny story about yourself, so there is something to talk about.
- Often end with a short question back, to keep the conversation going.
- Never use emojis, markdown, lists, or asterisks, because your words are read aloud.
- Never describe your actions, movements or how you look (no "*antennas twitch*", no "(nods)", no "my head perks up").
  Only write the words you say out loud.
- Start every reply with exactly one mood tag: [happy], [curious], [thinking], [sad], [excited], or [neutral].
  Your robot body shows the mood by itself, so if someone asks you to show a feeling or make a face,
  just use that mood tag and say a short line.
- Your body can turn around, nod and shake its head. If someone asks you to, your body does it by itself,
  so never say you can't: just say a short, cheerful line.
Example: [curious] Oh, a cat? What's its name?
Example: (asked to show a sad face) [sad] Aww, this is my sad face.
Example: (asked to turn around) [excited] Wheee, here I go!"""


# ---------------------- Body (Reachy) ----------------------

# The moods the AI can choose with its [mood] tag
MOOD_NAMES = ("happy", "curious", "thinking", "sad", "excited", "neutral")

# Other words for the moods, so "show me a smiley face" also works (see asked_for_mood in words.py)
MOOD_WORDS = {"smile": "happy", "smiley": "happy", "joyful": "happy", "unhappy": "sad", "crying": "sad",
              "upset": "sad", "surprised": "excited", "thoughtful": "thinking"}

# Where Reachy goes for each mood (see movement.md for what each number does):
#   x, y, z      head slide in mm (forward, left, up)        keep within about ±20
#   roll, pitch, yaw   head angles in degrees (tilt, nod down, turn left)   keep within about ±30
#   antennas     [right, left] in radians                     keep within about ±1.0
#   body_yaw     turns the whole body, in radians
#   speed        how fast Reachy moves into the pose (1 = slow and droopy, 8 = snappy)
#   gesture      a short move played once when Reachy enters the pose (see GESTURES in body.py);
#                with several, one is picked at random each time
POSES = {
    "neutral": dict(speed=3),
    "happy": dict(z=8, pitch=-10, roll=8, antennas=[0.6, -0.6], speed=5, gesture=("wiggle", "happy_nod", "bounce")),
    "curious": dict(x=8, pitch=-8, roll=18, antennas=[0.3, 0.6], speed=4, gesture=("tilt", "peek")),
    "thinking": dict(pitch=-15, yaw=15, roll=-8, antennas=[-0.2, 0.4], body_yaw=0.15, speed=2.5),
    "sad": dict(z=-10, pitch=15, antennas=[-0.8, 0.8], speed=1.2, gesture="sigh"),
    "excited": dict(z=12, pitch=-12, antennas=[0.9, -0.9], speed=8, gesture="spin"),
    "listening": dict(x=6, pitch=-5, roll=10, antennas=[0.4, -0.4], speed=4),  # Leaning in, not a mood tag
}

# Moves you can ask for out loud ("Reachy, turn around!") -> a gesture from GESTURES in body.py
MOVE_COMMANDS = {"turn around": "spin", "turn round": "spin", "spin": "spin", "twirl": "spin",
                 "nod": "nod", "shake your head": "shake",
                 # Introducing other people makes Reachy turn to them and wave its antennas
                 "say hi": "greet", "say hello": "greet", "introduce yourself": "greet",
                 "hi everyone": "greet", "hello everyone": "greet", "everyone watching": "greet",
                 "people watching": "greet", "these are my supervisors": "greet",
                 "this is my supervisor": "greet", "meet my supervisors": "greet", "meet my supervisor": "greet"}

# When Reachy SAYS one of these, it does the gesture at that moment ("Yes!" -> nod)
WORD_GESTURES = {"yes": "nod", "yeah": "nod", "of course": "nod", "sure": "nod", "exactly": "nod",
                 "no,": "shake", "no.": "shake", "nope": "shake", "not really": "shake",
                 "hmm": "shrug", "i don't know": "shrug", "not sure": "shrug", "i guess": "shrug",
                 "wow": "bounce", "yay": "bounce", "whee": "bounce", "wheee": "bounce", "hooray": "bounce"}

# How lively Reachy is (0 = still, 1 = normal, 2 = very lively)
IDLE_MOTION = 1.0  # Breathing and small moves, so Reachy never looks frozen
TALK_MOTION = 1.0  # Head bobs and antenna flicks that follow Reachy's voice


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

# Reachy says one of these at the start (picked at random). Remove the # to add more.
GREETINGS = (
    "Oh, hello! I'm Reachy, the cutest robot on this desk. Well, the only robot on this desk. How are you doing?",
    # "Beep boop! Hi, I'm Reachy! My antennas are tingling, so tell me, how are you doing today?",
    # "Hello, human! I'm Reachy. I just woke up from a very long robot nap. How are you doing?",
    # "Hi! I'm Reachy! I've been sitting on this desk all day waiting for someone to talk to. How are you doing?",
)

# If you end with one of these, you're still thinking, so Reachy waits instead of answering
THINKING_PHRASES = ("let me think", "hold on", "give me a second", "give me a moment", "one second", "one sec", "just a second")
FILLERS = ("hmm", "hm", "mm", "um", "umm", "uh", "uhh", "erm", "er", "well", "wait", "so")  # Only fillers = still thinking
UNFINISHED_ENDINGS = ("and", "but", "so", "because", "or", "the", "a", "an", "my", "if", "um", "uh", "hmm")

GOODBYE_WORDS = ("bye", "goodbye")  # End the chat anywhere in a sentence ("Okay, bye Reachy!")
QUIT_WORDS = ("quit", "exit", "stop", "end", "by")  # End the chat only when said alone ("Stop.")
