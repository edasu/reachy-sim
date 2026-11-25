# sim.py — Starts the 3D simulator, but lighter, so Reachy's voice and brain get more of the CPU.
#
# The normal simulator also films Reachy's own camera in HD 25 times a second and turns it into video.
# chat.py never uses that camera, so this script switches it off. Everything else is the same.
#
# Run it (in its own terminal):   .venv/bin/mjpython sim.py
# Extra options still work, e.g.  .venv/bin/mjpython sim.py --scene minimal

import sys

from reachy_mini.daemon.app.main import main
from reachy_mini.daemon.backend.mujoco.backend import MujocoBackend

MujocoBackend.rendering_loop = lambda self, camera_name, port: None  # No virtual camera

if "--sim" not in sys.argv:
    sys.argv.append("--sim")
if "--no-media" not in sys.argv:
    sys.argv.append("--no-media")  # No camera, audio or video streaming either

main()
