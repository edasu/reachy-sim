# ============================================================
# chat.py — Free conversation with Reachy Mini using Ollama
#
# How it works, in one loop:
#   1. You type a message
#   2. The whole conversation is sent to a local AI model (Ollama)
#   3. The model replies with a mood tag + text, e.g. "[happy] Nice to meet you!"
#   4. Reachy moves into that mood's pose and speaks the text out loud
#   5. Repeat until you say "bye"
# ============================================================

import json  # Converts Python data to/from JSON text (the format Ollama uses)
import re  # "Regular expressions": finds text patterns, like the [mood] tag
import subprocess  # Runs the macOS `say` command for voice output
import urllib.error  # Error types for web requests, so we can catch them
import urllib.request  # Sends HTTP requests to Ollama (built into Python, nothing to install)
from reachy_mini import ReachyMini  # Main client to connect to the Reachy Mini simulator
from reachy_mini.utils import create_head_pose  # Helper to build head positions and angles


# ---------------------- Settings ----------------------

VOICE = "Stephanie (Enhanced)"  # macOS voice name (check options with `say -v "?"`)
RATE = 155  # Speaking speed in words per minute

# Ollama runs a small web server on your own Mac.
# 11434 is Ollama's port, and /api/chat is the address for chat-style conversations.
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2"  # Any model you've downloaded with `ollama pull <name>`

# The "system prompt": hidden instructions that shape Reachy's personality.
# The model reads this at the start of every request, but it's never spoken aloud.
# Change this text to change how Reachy talks (cute, grumpy, Turkish, etc.).
# The triple quotes """ let a string span several lines.
SYSTEM_PROMPT = """You are Reachy Mini, a small, friendly, cute,curious desktop robot with a head and two antennas.
You are having a casual spoken conversation, so:
- Reply in 1 or 2 short sentences, like a real person chatting.
- Never use emojis, markdown, lists, or asterisks, because your words are read aloud.
- Start every reply with exactly one mood tag: [happy], [curious], [thinking], [sad], [excited], or [neutral].
Example: [curious] Oh, a cat? What's its name?"""

# Body language for each mood. Each entry is a dictionary with:
MOODS = {
    "happy": dict(head=create_head_pose(z=8, pitch=-10, roll=8, mm=True), antennas=[0.6, -0.6]),  # Head up, small tilt
    "curious": dict(head=create_head_pose(x=8, pitch=-8, roll=18, mm=True), antennas=[0.3, 0.6]),  # Lean in, big tilt
    "thinking": dict(head=create_head_pose(pitch=-15, yaw=15, roll=-8, mm=True), antennas=[-0.2, 0.4]),  # Look up and away
    "sad": dict(head=create_head_pose(z=-10, pitch=15, mm=True), antennas=[-0.8, 0.8]),  # Sink down, look down
    "excited": dict(head=create_head_pose(z=12, pitch=-12, mm=True), antennas=[0.9, -0.9]),  # Rise up, antennas wide
    "neutral": dict(head=create_head_pose(), antennas=[0.0, 0.0]),  # Everything at 0 = centered
}

# If any of these words is in your message, Reachy answers one last time, then the chat ends
QUIT_WORDS = ("bye", "goodbye", "quit", "exit", "stop", "end", "by")


# ---------------------- Helper functions ----------------------

def speak(text: str) -> None:
    print(f"Reachy: {text}")  # Also shows Reachy's words in the terminal
    # `subprocess.run` waits until speech finishes, so Reachy doesn't start listening while still talking
    subprocess.run(["say", "-v", VOICE, "-r", str(RATE), text])


def ask_ollama(messages: list[dict]) -> str:
    # The AI model has no memory of its own: we send the WHOLE conversation every time,
    # so it can "remember" what was said earlier.
    # json.dumps turns the Python dictionary into JSON text; .encode() turns that text into bytes for sending.
    # "stream": False = wait for the full answer at once (instead of word by word).
    body = json.dumps({"model": MODEL, "messages": messages, "stream": False}).encode()

    # Build a POST request (because it has data) and tell Ollama the data is JSON
    request = urllib.request.Request(OLLAMA_URL, data=body, headers={"Content-Type": "application/json"})

    # Send it and wait up to 120 seconds for the answer
    with urllib.request.urlopen(request, timeout=120) as response:
        # Ollama replies with JSON like: {"message": {"role": "assistant", "content": "[happy] Hi!"}, ...}
        # json.loads turns it back into a Python dictionary, and we pick out just the text
        return json.loads(response.read())["message"]["content"]


def split_mood(reply: str) -> tuple[str, str]:
    # Turns "[happy] Hi there!" into ("happy", "Hi there!"). Falls back to neutral if no valid tag.
    #
    # The pattern r"\s*\[(\w+)\]\s*" means:
    #   \s*     any spaces at the start
    #   \[ \]   the literal square brackets
    #   (\w+)   one or more letters inside them, "captured" so we can read them as group(1)
    #   \s*     any spaces after the tag
    # re.match only looks at the START of the text.
    match = re.match(r"\s*\[(\w+)\]\s*", reply)

    # Use the tag only if it's one of our known moods (the model might invent "[giggly]")
    if match and match.group(1).lower() in MOODS:
        # match.end() is where the tag ends, so reply[match.end():] is everything after it
        return match.group(1).lower(), reply[match.end():].strip()

    # No valid tag: use the neutral pose, and remove any [tags] anywhere so they aren't read aloud
    return "neutral", re.sub(r"\[\w+\]", "", reply).strip()


def move(mini: ReachyMini, mood: str, duration: float = 0.7) -> None:
    # `**MOODS[mood]` unpacks the dictionary, so this becomes:
    #   mini.goto_target(head=..., antennas=..., duration=...)
    # `duration` has a default of 0.7 seconds, but you can pass a different value
    mini.goto_target(**MOODS[mood], duration=duration)


# ---------------------- Main program ----------------------

# Conversation history (the AI's "memory"). Each message has a role:
#   "system"    = the hidden personality instructions (always first)
#   "user"      = what you typed
#   "assistant" = what Reachy answered
messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# Opens a connection to the running Reachy Mini simulation and closes it cleanly at the end
with ReachyMini() as mini:
    move(mini, "happy")
    speak("Hi! I'm Reachy. Let's chat. Say bye whenever you want to stop.")

    # `while True` repeats forever, until a `break` line stops it
    while True:
        move(mini, "curious", 0.5)  # Listening pose while you type
        user_text = input("You: ").strip()  # Wait for your message; .strip() removes extra spaces
        if not user_text:
            continue  # Empty message: skip the rest and go back to the top of the loop

        messages.append({"role": "user", "content": user_text})  # Add your message to the memory
        move(mini, "thinking", 0.5)  # Looks thoughtful while the model is generating

        # `try` runs code that might fail; `except` decides what to do if it does
        try:
            reply = ask_ollama(messages)
        except urllib.error.HTTPError as error:
            # Ollama answered, but with an error (e.g. model not downloaded)
            print(f"Ollama error: {json.loads(error.read()).get('error', error)}")
            print(f"Tip: download the model with `ollama pull {MODEL}`")
            speak("Hmm, my brain gave me an error. Check the terminal.")
            break  # Leave the loop
        except urllib.error.URLError:
            # Couldn't connect at all (Ollama app not running)
            speak("Hmm, I can't reach my brain. Is Ollama running?")
            break

        messages.append({"role": "assistant", "content": reply})  # Remember Reachy's own answer too
        mood, text = split_mood(reply)  # e.g. mood="happy", text="Nice to meet you!"
        move(mini, mood)  # Show the emotion...
        speak(text)  # ...then say the words (without the [tag])

        # .split() breaks your message into separate words, so we compare whole words.
        # `any(...)` is True if at least one quit word is among them.
        if any(word in user_text.lower().split() for word in QUIT_WORDS):
            break  # Stop after Reachy says goodbye

    move(mini, "neutral", 0.8)  # Return to the center before closing
