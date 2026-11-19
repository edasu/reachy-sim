import subprocess
import time
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

VOICE = "Yelda"  # Change if `say -v "?" | grep "tr_TR"` shows another Turkish voice name
RATE = 180

def speak(text: str):
    subprocess.Popen(["say", "-v", VOICE, "-r", str(RATE), text])

with ReachyMini() as mini:
    speak("Merhaba!")
    mini.goto_target(
        head=create_head_pose(pitch=-10, yaw=12, roll=8, degrees=True),
        antennas=[0.7, -0.4],
        duration=0.8,
    )
    time.sleep(0.9)

    speak("Nasılsın?")
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
