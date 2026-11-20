import subprocess  # Lets Python run macOS terminal commands like `say`
import time  # Lets us pause between movements so actions don't overlap
from reachy_mini import ReachyMini  # Main client to connect to the Reachy Mini daemon/simulator
from reachy_mini.utils import create_head_pose  # Helper to build head angles (pitch, yaw, roll)

VOICE = "Samantha"  # macOS voice name (check options with `say -v "?"`)
RATE = 185  # Speaking speed in words per minute


def speak(text: str) -> None:
    # Starts `say` in the background (`Popen`) so Reachy Mini can move while speaking
    subprocess.Popen(["say", "-v", VOICE, "-r", str(RATE), text])


# Opens a connection to the running Reachy Mini simulation and closes it cleanly at the end
with ReachyMini() as mini:
    # Say "Hello!" while tilting/turning the head and swinging the antennas
    speak("Hello!")
    mini.goto_target(
        head=create_head_pose(pitch=-10, yaw=12, roll=8, degrees=True),
        antennas=[0.7, -0.4],
        duration=0.8,  # Time (in seconds) for this smooth transition
    )
    time.sleep(0.9)  # Hold/wait briefly before the next phrase

    # Ask "How are you?" with a curious head roll and opposite antenna pose
    speak("How are you?")
    mini.goto_target(
        head=create_head_pose(pitch=-12, yaw=10, roll=18, degrees=True),
        antennas=[-0.5, 0.5],
        duration=1.0,
    )
    time.sleep(1.4)

    # Smoothly return head and both antennas back to their neutral center position
    mini.goto_target(
        head=create_head_pose(pitch=0, yaw=0, roll=0, degrees=True),
        antennas=[0.0, 0.0],
        duration=1.0,
    )
