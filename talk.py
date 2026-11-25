import random
import re
import subprocess
import time
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

VOICE = "Stephanie (Enhanced)"  # macOS voice name (must be downloaded; check with `say -v "?"`)
RATE = 175  # Speaking speed in words per minute (lower = slower, calmer)


def speak(text: str) -> None:
    print(f"Reachy: {text}")  # Also shows Reachy's words in the terminal
    # Wait until speech finishes so Reachy doesn't talk over itself or start listening early
    subprocess.run(["say", "-v", VOICE, "-r", str(RATE), text])


# Opens a connection to the running Reachy Mini simulation and closes it cleanly at the end
with ReachyMini() as mini:
    # Friendly greeting with a small head tilt
    mini.goto_target(
        head=create_head_pose(pitch=-10, yaw=10, roll=8, degrees=True),  # Head angles in degrees
        antennas=[0.5, -0.4],  # [right, left] antenna angles in radians
        duration=0.7,  # Time (in seconds) for this smooth movement
    )
    # `random.choice` picks one greeting from the list, so it's not the same every time
    speak(random.choice(["Hey there!", "Oh, hi! Good to see you."]))

    # Listen pose (slight head tilt)
    mini.goto_target(
        head=create_head_pose(pitch=-5, yaw=0, roll=14, degrees=True),
        antennas=[0.2, 0.2],
        duration=0.6,
    )
    # Waits for you to type; `.strip().lower()` removes extra spaces and makes it lowercase
    user_greeting = input("You: ").strip().lower()

    # React naturally and ask how they're doing
    mini.goto_target(
        head=create_head_pose(pitch=-11, yaw=-6, roll=-6, degrees=True),
        antennas=[-0.4, 0.4],
        duration=0.7,
    )
    # Splits your text into whole words, so "hi" doesn't match inside "this" or "nothing"
    greeting_words = re.findall(r"\w+", user_greeting)
    # `any(...)` is True if at least one greeting word (English or Turkish) is in your text
    if any(word in greeting_words for word in ("hi", "hey", "hello", "merhaba", "selam")):
        speak("Hey! ... How's your day going?")  # "..." makes the voice pause briefly
    else:
        speak("Gotcha. ... How are you doing today?")

    # Wait for reply
    mini.goto_target(
        head=create_head_pose(pitch=-5, yaw=0, roll=14, degrees=True),
        antennas=[0.2, 0.2],
        duration=0.6,
    )
    user_reply = input("You: ").strip().lower()

    # Respond warmly if asked back
    mini.goto_target(
        head=create_head_pose(pitch=-12, yaw=6, roll=4, degrees=True),
        antennas=[0.5, -0.5],
        duration=0.7,
    )
    # Checks if you asked Reachy "how are you" back (including short forms and Turkish)
    if any(phrase in user_reply for phrase in ("how are you", "how r u", "hows u", "you?", "and you", "nasılsın")):
        speak(
            random.choice(  # Picks one of these two answers at random
                [
                    "I'm doing pretty well, thanks for asking! What are we working on?",
                    "Pretty good over here! ... Thanks for asking. How can I help?",
                ]
            )
        )
    else:
        speak("Nice, glad to hear that! Whenever you're ready, I'm right here.")

    time.sleep(0.4)  # Short pause before going back to rest
    # Return head and antennas to the neutral center position
    mini.goto_target(
        head=create_head_pose(pitch=0, yaw=0, roll=0, degrees=True),
        antennas=[0.0, 0.0],
        duration=0.8,
    )
