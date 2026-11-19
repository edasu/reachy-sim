import time
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

with ReachyMini() as mini:
    print("Connected! Moving Reachy Mini...")
    mini.goto_target(antennas=[1.0, -1.0], duration=0.8)
    mini.goto_target(
        head=create_head_pose(pitch=-25, yaw=30, roll=15, degrees=True),
        duration=1.0,
    )
    time.sleep(1.0)

    mini.goto_target(antennas=[-1.0, 1.0], duration=0.8)
    mini.goto_target(
        head=create_head_pose(pitch=15, yaw=-30, roll=-15, degrees=True),
        duration=1.0,
    )
    time.sleep(1.0)

    # Return to center
    mini.goto_target(
        head=create_head_pose(),
        antennas=[0.0, 0.0],
        duration=1.0,
    )
