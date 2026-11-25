# body.py — Reachy's body: moves the head, antennas and body so Reachy always looks alive.
#
# A background loop updates the robot 50 times per second. Each update adds up 4 layers:
#   1. Pose      where Reachy is heading (a mood from settings.POSES), reached smoothly at the pose's speed
#   2. Idle      slow breathing plus a small move that fits the pose, so Reachy never freezes
#   3. Talking   head bobs and antenna flicks that follow how loud Reachy's voice is
#   4. Gesture   a short one-off move like a nod or a bounce

import math
import random
import threading
import time

from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

from . import settings
from .voice import Voice

UPDATES_PER_SECOND = 50
PARTS = ("x", "y", "z", "roll", "pitch", "yaw", "right", "left", "body_yaw")  # Everything Reachy can move
LIMITS = dict(x=20, y=20, z=20, roll=30, pitch=30, yaw=35, right=1.2, left=1.2, body_yaw=2.6)  # Safety limits (the body can turn about ±150°)


def wave(t: float, seconds: float) -> float:
    # Smooth back-and-forth between -1 and 1, once every `seconds`
    return math.sin(2 * math.pi * t / seconds)


def ease(u: float) -> float:
    # 0 -> 1 that starts and ends gently (no sudden jerk)
    return 0.5 - 0.5 * math.cos(math.pi * u)


# Short one-off moves. Each takes u = progress from 0 to 1 and returns what to add to the pose.
# (1 - u) makes the move fade out at the end.
GESTURES = {
    "nod": (0.6, lambda u: dict(pitch=9 * abs(math.sin(2 * math.pi * u)))),  # Two small nods: "mm-hm, go on"
    "wiggle": (0.9, lambda u: dict(right=0.5 * wave(u, 1 / 3) * (1 - u), left=0.5 * wave(u, 1 / 3) * (1 - u))),  # Happy antenna wag
    "bounce": (0.9, lambda u: dict(z=8 * abs(math.sin(3 * math.pi * u)) * (1 - u),  # Three little hops
                                   right=0.4 * wave(u, 0.25) * (1 - u), left=-0.4 * wave(u, 0.25) * (1 - u))),
    "tilt": (1.2, lambda u: dict(roll=14 * wave(u, 1) * (1 - u))),  # Curious tilt one way, then the other
    "shake": (0.8, lambda u: dict(yaw=15 * wave(u, 0.5) * (1 - u))),  # "No no"
    # Turns the whole body around to the left, then to the right, then back, with happy hops and antennas
    # Answers that match Reachy's words (see WORD_GESTURES in settings.py)
    "happy_nod": (0.8, lambda u: dict(pitch=8 * abs(math.sin(2 * math.pi * u)),  # Nod with antennas up
                                      right=0.4 * math.sin(math.pi * u), left=-0.4 * math.sin(math.pi * u))),
    "shrug": (1.4, lambda u: dict(roll=12 * math.sin(math.pi * u),  # "I don't know": tilt, antennas uneven
                                  right=0.5 * math.sin(math.pi * u), left=0.5 * math.sin(math.pi * u))),
    "sigh": (1.8, lambda u: dict(z=-5 * math.sin(math.pi * u), pitch=8 * math.sin(math.pi * u),  # Slow droop and back
                                 right=-0.3 * math.sin(math.pi * u), left=0.3 * math.sin(math.pi * u))),
    "peek": (1.4, lambda u: dict(x=5 * math.sin(math.pi * u), yaw=14 * wave(u, 1) * (1 - u))),  # Curious look around
    # While you talk: small "mm-hm" moves
    "listen_nod": (0.5, lambda u: dict(pitch=5 * math.sin(math.pi * u), right=0.15 * math.sin(2 * math.pi * u))),
    "listen_tilt": (0.9, lambda u: dict(roll=6 * math.sin(math.pi * u), left=-0.15 * math.sin(2 * math.pi * u))),
    # Turns to the audience (e.g. your supervisors), waves its antennas, then turns back to you
    "greet": (3.5, lambda u: dict(body_yaw=0.9 * math.sin(math.pi * ease(u)), pitch=-6 * math.sin(math.pi * u),
                                  right=0.5 * wave(u, 0.15) * math.sin(math.pi * u),
                                  left=-0.5 * wave(u, 0.15) * math.sin(math.pi * u))),
    "spin": (5.0, lambda u: dict(body_yaw=2.5 * math.sin(2 * math.pi * ease(u)),
                                 z=5 * abs(math.sin(8 * math.pi * u)) * (1 - u),
                                 right=0.4 * wave(u, 0.1), left=-0.4 * wave(u, 0.1))),
}


def idle_motion(pose_name: str, t: float) -> dict:
    # Small, slow moves that keep Reachy looking alive. Different for each pose.
    move = dict(z=1.5 * wave(t, 4), right=0.05 * wave(t, 3), left=-0.05 * wave(t, 3))  # Breathing
    extra = {
        "listening": dict(roll=3 * wave(t, 5), pitch=1.5 * wave(t, 7)),  # Gentle, attentive sway
        "thinking": dict(yaw=7 * wave(t, 6), pitch=-3 * abs(wave(t, 6)), right=0.15 * wave(t, 2.5)),  # Looks around
        "curious": dict(roll=4 * wave(t, 3)),  # Little tilts
        "happy": dict(right=0.15 * wave(t, 0.8), left=-0.15 * wave(t, 0.8)),  # Antennas dance
        "excited": dict(z=2 * abs(wave(t, 1.2)), right=0.25 * wave(t, 0.4), left=-0.25 * wave(t, 0.4)),  # Bouncy
        "sad": dict(pitch=1.5 * wave(t, 6), roll=2 * wave(t, 9)),  # Slow, heavy sway
    }.get(pose_name, {})
    for part, value in extra.items():
        move[part] = move.get(part, 0) + value
    return move


def talking_motion(level: float, t: float) -> dict:
    # level = how loud Reachy is right now (0 to 1). Louder syllables = bigger head bobs.
    return dict(
        pitch=-5 * level,  # Lifts the head a little on each loud syllable
        z=2 * level,
        roll=2 * wave(t, 2.3) * level,
        right=0.25 * level * wave(t, 0.3),  # Antenna flicks
        left=-0.25 * level * wave(t, 0.37),
        body_yaw=0.06 * wave(t, 3.5) * min(1, level * 3),  # Slow body sway while talking
    )


class Body:
    # Use it with `with`: it starts moving at the start and goes back to rest at the end.
    #   with Body(mini, voice) as body:
    #       body.set_pose("happy")
    #       body.gesture("nod")

    def __init__(self, mini: ReachyMini, voice: Voice):
        self.mini = mini
        self.voice = voice
        self.current = {part: 0.0 for part in PARTS}  # Where the pose layer is right now
        self.pose_name = "neutral"
        self.gesture_name, self.gesture_started = None, 0.0
        self.talk_level = 0.0
        self.running = False
        self.ears = None  # Set by chat.py, so Reachy can nod while you talk
        self.next_listen_move = 0.0

    def __enter__(self) -> "Body":
        self.mini.goto_target(head=create_head_pose(), antennas=[0.0, 0.0], duration=1.0)  # Start from neutral
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *error) -> None:
        self.set_pose("neutral")
        time.sleep(1.2)  # Let Reachy settle back to neutral
        self.running = False
        self.thread.join()

    # ---------- What chat.py uses ----------

    def set_pose(self, name: str) -> None:
        # Starts moving smoothly to a pose from settings.POSES, and plays its gesture (if it has one).
        # A pose can list several gestures: one is picked at random, so Reachy doesn't look repetitive.
        self.pose_name = name
        gesture = settings.POSES[name].get("gesture")
        if isinstance(gesture, tuple):
            gesture = random.choice(gesture)
        if gesture:
            self.gesture(gesture)

    def gesture(self, name: str) -> None:
        # Plays a short move from GESTURES on top of the current pose.
        # A long gesture that is still playing (a spin, a greeting) is never cut off by a new one.
        if self.gesture_name:
            seconds = GESTURES[self.gesture_name][0]
            if seconds >= 2 and time.perf_counter() - self.gesture_started < seconds:
                return
        self.gesture_name, self.gesture_started = name, time.perf_counter()

    def gesture_after(self, name: str, seconds: float) -> None:
        # Plays a gesture a bit later, e.g. a nod exactly when Reachy says "yes"
        timer = threading.Timer(seconds, self.gesture, args=[name])
        timer.daemon = True
        timer.start()

    # ---------- The animation loop ----------

    def _target(self) -> dict:
        pose = settings.POSES[self.pose_name]
        antennas = pose.get("antennas", [0.0, 0.0])
        return {part: pose.get(part, 0.0) for part in PARTS} | dict(right=antennas[0], left=antennas[1])

    def _loop(self) -> None:
        start = last = time.perf_counter()
        while self.running:
            now = time.perf_counter()
            dt, t, last = now - last, now - start, now

            # 1. Pose: move a bit closer to the target pose every update (smooth, at the pose's speed)
            target, speed = self._target(), settings.POSES[self.pose_name].get("speed", 4)
            blend = 1 - math.exp(-speed * dt)
            for part in PARTS:
                self.current[part] += (target[part] - self.current[part]) * blend
            final = dict(self.current)

            # 2. Idle, 3. Talking: follow the voice, rising fast and falling a bit slower (looks natural)
            level = self.voice.loudness()
            self.talk_level += (level - self.talk_level) * (0.6 if level > self.talk_level else 0.25)
            layers = [
                (idle_motion(self.pose_name, t), settings.IDLE_MOTION),
                (talking_motion(self.talk_level, t), settings.TALK_MOTION),
            ]

            # While you talk, Reachy gives small nods and tilts now and then, like "mm-hm, go on"
            if self.pose_name == "listening" and self.ears and self.ears.hearing_you and now >= self.next_listen_move:
                self.gesture(random.choice(("listen_nod", "listen_tilt")))
                self.next_listen_move = now + random.uniform(1.5, 3.0)

            # 4. Gesture
            if self.gesture_name:
                seconds, move = GESTURES[self.gesture_name]
                progress = (now - self.gesture_started) / seconds
                if progress < 1:
                    layers.append((move(progress), 1.0))
                else:
                    self.gesture_name = None

            for moves, strength in layers:
                for part, value in moves.items():
                    final[part] += value * strength

            self._send(final)
            time.sleep(max(0.0, 1 / UPDATES_PER_SECOND - (time.perf_counter() - now)))

    def _send(self, p: dict) -> None:
        p = {part: max(-LIMITS[part], min(LIMITS[part], value)) for part, value in p.items()}  # Stay safe
        # The head's yaw is measured from where the body points, so the head turns along with the body
        head_yaw = p["yaw"] + math.degrees(p["body_yaw"])
        head = create_head_pose(x=p["x"], y=p["y"], z=p["z"], roll=p["roll"], pitch=p["pitch"], yaw=head_yaw,
                                mm=True, degrees=True)
        try:
            self.mini.set_target(head=head, antennas=[p["right"], p["left"]], body_yaw=p["body_yaw"])
        except Exception as error:  # Don't crash the chat if one update fails
            print(f"(movement error: {error})")
            time.sleep(0.5)
