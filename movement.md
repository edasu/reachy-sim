# Reachy Mini Movement Guide

A quick reference for moving Reachy Mini's head, antennas and body, plus a library of ready-made expressions to copy.

---

## 1. The basics

```python
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

with ReachyMini() as mini:
    mini.goto_target(
        head=create_head_pose(pitch=-10, roll=10, degrees=True),
        antennas=[0.5, -0.5],
        duration=0.8,
    )
```

Every movement is one `goto_target(...)` call. It **waits until the move is finished** before the next line runs, so you don't need `time.sleep()` to wait for movement, only to *hold* a pose or to wait for speech.

---

## 2. `create_head_pose(...)` — where the head goes

```python
create_head_pose(x=0, y=0, z=0, roll=0, pitch=0, yaw=0, mm=False, degrees=True)
```

### Rotation (angles)

| Argument | Motion | Positive value | Negative value |
|---|---|---|---|
| `pitch` | Nod | Looks **down** | Looks **up** |
| `yaw` | Turn | Turns to Reachy's **left** | Turns to Reachy's **right** |
| `roll` | Tilt (head to shoulder) | Tilts to Reachy's **right** | Tilts to Reachy's **left** |

- Angles are in **degrees** by default (`degrees=True`).
- Good range to stay in: about **-30° to 30°**.

> The positive/negative directions come from the math in the library (x forward, y left, z up). If one looks backwards in the simulator, flip the sign.

### Position (sliding the head)

| Argument | Motion | Positive value | Negative value |
|---|---|---|---|
| `x` | Forward / back | Leans **forward** | Pulls **back** |
| `y` | Side to side | Shifts to Reachy's **left** | Shifts to Reachy's **right** |
| `z` | Up / down | Rises **up** | Sinks **down** |

- **Always add `mm=True`** when you use `x`, `y` or `z`. Without it the numbers are in **meters**, so `z=10` would mean 10 meters.
- Keep these small: about **-20 to 20 mm**. The head can only slide a little.

```python
create_head_pose(z=10, mm=True)               # raise the head by 1 cm
create_head_pose(x=10, pitch=-5, mm=True)     # lean forward and look slightly up
create_head_pose()                            # neutral: everything at 0
```

---

## 3. `goto_target(...)` — how it moves

```python
mini.goto_target(head=..., antennas=..., duration=0.5, method="minjerk", body_yaw=0.0)
```

| Argument | What it does |
|---|---|
| `head` | Target head pose from `create_head_pose(...)` |
| `antennas` | `[right, left]` antenna angles, in **radians** |
| `duration` | Seconds the move takes (must be more than 0) |
| `method` | Movement style (see below) |
| `body_yaw` | Turns the **whole body**, in **radians**. Default `0.0` = back to center. Use `None` to keep the body where it is. |

You can leave out `head` or `antennas` to move only one of them.

### Antennas

- Order is **`[right, left]`** (Reachy's right and left).
- Values are in **radians**: `0.5` ≈ 30°, `1.0` ≈ 57°.
- Good range: about **-1.0 to 1.0**.
- `[0, 0]` = straight up (neutral).
- **Opposite signs** (`[0.6, -0.6]`) and **same signs** (`[0.6, 0.6]`) look different: one makes the antennas mirror each other, the other makes them lean the same way. Try both in the simulator and write down which is which for you.

### Movement styles (`method`)

| Value | Feel |
|---|---|
| `"minjerk"` | Smooth and natural (default) |
| `"linear"` | Constant speed, robotic |
| `"ease_in_out"` | Slow start, fast middle, slow end |
| `"cartoon"` | Bouncy, playful, overshoots a little |

```python
mini.goto_target(head=create_head_pose(z=10, mm=True), duration=0.6, method="cartoon")
```

### Duration guide

| Duration | Feels like |
|---|---|
| `0.2 – 0.4` | Quick, surprised, energetic |
| `0.5 – 0.8` | Normal, friendly |
| `1.0 – 2.0` | Slow, sleepy, sad, thoughtful |

---

## 4. Other useful methods

| Method | What it does |
|---|---|
| `mini.wake_up()` | Built-in wake-up animation |
| `mini.goto_sleep()` | Built-in go-to-sleep animation |
| `mini.look_at_world(x, y, z, duration=1.0)` | Turns the head to look at a point in space (meters) |
| `mini.set_target(head=..., antennas=...)` | Jumps **instantly** (no smooth move). Useful in fast loops |
| `mini.get_current_head_pose()` | Returns where the head is right now |
| `mini.get_present_antenna_joint_positions()` | Returns the current antenna angles |

---

## 5. Expression library

Copy any of these. Each one is a single `goto_target` call unless it says otherwise.

### Neutral / rest
```python
mini.goto_target(head=create_head_pose(), antennas=[0.0, 0.0], duration=0.8)
```

### Happy
```python
mini.goto_target(
    head=create_head_pose(z=8, pitch=-10, roll=8, mm=True),
    antennas=[0.6, -0.6],
    duration=0.7,
)
```

### Excited
Quick, raised, antennas wide.
```python
mini.goto_target(
    head=create_head_pose(z=12, pitch=-12, mm=True),
    antennas=[0.9, -0.9],
    duration=0.4,
    method="cartoon",
)
```

### Curious
Head tilt plus a small lean forward.
```python
mini.goto_target(
    head=create_head_pose(x=8, pitch=-8, roll=18, mm=True),
    antennas=[0.3, 0.6],
    duration=0.6,
)
```

### Listening
```python
mini.goto_target(
    head=create_head_pose(pitch=-5, roll=14),
    antennas=[0.2, 0.2],
    duration=0.6,
)
```

### Thinking
Looks up and to the side.
```python
mini.goto_target(
    head=create_head_pose(pitch=-15, yaw=15, roll=-8),
    antennas=[-0.2, 0.4],
    duration=0.8,
)
```

### Sad
Slow, head down and sunk, antennas drooping.
```python
mini.goto_target(
    head=create_head_pose(z=-10, pitch=15, mm=True),
    antennas=[-0.8, 0.8],
    duration=1.5,
)
```

### Shy
Sinks a little, turns away and looks down.
```python
mini.goto_target(
    head=create_head_pose(z=-8, pitch=10, yaw=-15, roll=5, mm=True),
    antennas=[-0.3, 0.3],
    duration=1.0,
)
```

### Surprised
Fast pull back and up.
```python
mini.goto_target(
    head=create_head_pose(x=-10, z=10, pitch=-10, mm=True),
    antennas=[1.0, -1.0],
    duration=0.25,
)
```

### Sleepy
Slow droop.
```python
mini.goto_target(
    head=create_head_pose(z=-12, pitch=20, roll=10, mm=True),
    antennas=[-0.9, 0.9],
    duration=2.0,
    method="ease_in_out",
)
```

### Look around (whole body)
```python
mini.goto_target(head=create_head_pose(yaw=10), body_yaw=0.5, duration=1.0)    # turn left
mini.goto_target(head=create_head_pose(yaw=-10), body_yaw=-0.5, duration=1.2)  # turn right
mini.goto_target(head=create_head_pose(), body_yaw=0.0, duration=1.0)          # back to center
```

---

## 6. Gestures (several moves in a row)

### Nod "yes"
```python
for _ in range(2):
    mini.goto_target(head=create_head_pose(pitch=15), duration=0.25)
    mini.goto_target(head=create_head_pose(pitch=-5), duration=0.25)
mini.goto_target(head=create_head_pose(), duration=0.3)
```

### Shake "no"
```python
for _ in range(2):
    mini.goto_target(head=create_head_pose(yaw=20), duration=0.25)
    mini.goto_target(head=create_head_pose(yaw=-20), duration=0.25)
mini.goto_target(head=create_head_pose(), duration=0.3)
```

### Antenna wiggle (happy wag)
```python
for _ in range(3):
    mini.goto_target(antennas=[0.7, 0.7], duration=0.15)
    mini.goto_target(antennas=[-0.7, -0.7], duration=0.15)
mini.goto_target(antennas=[0.0, 0.0], duration=0.3)
```

### Confused (tilt one way, then the other)
```python
mini.goto_target(head=create_head_pose(roll=20, pitch=-5), antennas=[0.6, 0.0], duration=0.5)
mini.goto_target(head=create_head_pose(roll=-20, pitch=-5), antennas=[0.0, -0.6], duration=0.6)
mini.goto_target(head=create_head_pose(), antennas=[0.0, 0.0], duration=0.5)
```

---

## 7. Moving while talking

`goto_target` waits until it's done, so the order you write things in matters.

```python
import subprocess

# Talk AND move at the same time: start speech in the background first
subprocess.Popen(["say", "Hello!"])          # Popen = don't wait
mini.goto_target(head=create_head_pose(roll=10), duration=0.8)

# Talk THEN move: wait for speech to finish
subprocess.run(["say", "Hello!"])            # run = wait until done
mini.goto_target(head=create_head_pose(), duration=0.8)
```

---

## 8. Reusable mood dictionary

Keep all your expressions in one place and call them by name. This is the pattern [chat.py](chat.py) uses.

```python
MOODS = {
    "happy":   dict(head=create_head_pose(z=8, pitch=-10, roll=8, mm=True), antennas=[0.6, -0.6]),
    "curious": dict(head=create_head_pose(x=8, pitch=-8, roll=18, mm=True), antennas=[0.3, 0.6]),
    "sad":     dict(head=create_head_pose(z=-10, pitch=15, mm=True), antennas=[-0.8, 0.8]),
    "neutral": dict(head=create_head_pose(), antennas=[0.0, 0.0]),
}

def move(mini, mood, duration=0.7):
    mini.goto_target(**MOODS[mood], duration=duration)

move(mini, "happy")
move(mini, "sad", duration=1.5)
```

`**MOODS[mood]` unpacks the dictionary, so `head=` and `antennas=` are passed in automatically.

---

## 9. Common mistakes

| Problem | Cause | Fix |
|---|---|---|
| Head flies off or errors with `x`/`y`/`z` | Missing `mm=True` (numbers read as meters) | Add `mm=True` |
| Antennas barely move or spin wildly | Using degrees for antennas | Antennas are **radians**: use about -1.0 to 1.0 |
| Body keeps snapping back to center | `body_yaw` defaults to `0.0` | Pass `body_yaw=None` to keep its current turn |
| `ValueError` about duration | `duration=0` | Use `set_target(...)` for instant moves |
| `MoveBusyError` | Another move is still running (dashboard, other script) | Wait or stop the other script |
| Robot moves before speech ends | Used `Popen` | Use `subprocess.run` to wait for speech |
