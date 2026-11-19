import subprocess
import time
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

VOICE = "Samantha"  # Try "Daniel", "Karen", "Moira", or an Enhanced/Premium voice from `say -v "?"`
RATE = 185          # Words per minute (try 160-210)

def speak(text: str):
    subprocess.Popen(["say", "-v", VOICE, "-r", str(RATE), text])

with ReachyMini() as mini:
    speak("Hello!")
    mini.goto_target(
        head=create_head_pose(pitch=-10, yaw=12, roll=8, degrees=True),
        antennas=[0.7, -0.4],
        duration=0.8,
    )
    time.sleep(0.9)

    speak("How are you?")
    mini.goto_target(
        head=create_head_pose(pitch=-12, yaw=10, roll=18, degrees=True),
        antennas=[-0.5, 0.5],
        duration=1.0,
    )
    time.sleep(1.4)

    mini.goto_target(
        head=create_head_pose(pitch=0, yaw=0, roll=0, degrees=True),
        antennas=[0.0, 0.0],
        duration=1.0,
    )
