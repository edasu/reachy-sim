# voice.py — Reachy's voice: turns text into speech with Kokoro and plays it.

import hashlib
import logging

import numpy as np
import sounddevice as sd
from kokoro_onnx import Kokoro  # Offline text-to-speech

from . import settings

# Hide the harmless "words count mismatch" warning Kokoro's phonemizer prints for every sentence
logging.getLogger("phonemizer").setLevel(logging.ERROR)

# Kokoro is slow the first times it meets new sentence lengths (3+ s), then fast (under 1 s).
# Speaking one long sentence at startup, silently, makes every real reply fast.
WARM_UP_SENTENCE = ("Hi! I'm Reachy, a little robot, and I really love chatting with people about their day, "
                    "their hobbies, their pets, and all the fun things they are curious about.")


class Voice:
    def __init__(self):
        print("Loading Reachy's voice...")
        self.kokoro = Kokoro(settings.KOKORO_MODEL, settings.KOKORO_VOICES)  # Load once, reuse for every sentence
        self.play_rate = int(24000 * settings.PITCH)  # Kokoro makes 24 kHz audio; playing it faster raises the pitch
        self.lang = "en-gb" if settings.VOICE.startswith("b") else "en-us"
        self.prepare(WARM_UP_SENTENCE)

    def prepare(self, text: str, cache: bool = False) -> np.ndarray:
        # Turns text into audio, without playing it.
        # Pitch trick: generate slower speech, then play it PITCH times faster.
        # cache=True saves the audio in .voice_cache, so fixed phrases are instant next time.
        key = f"{settings.VOICE}|{settings.PITCH}|{settings.SPEED}|{text}"
        cache_file = settings.VOICE_CACHE / (hashlib.md5(key.encode()).hexdigest() + ".npy")
        if cache and cache_file.exists():
            return np.load(cache_file)

        samples, _ = self.kokoro.create(text, voice=settings.VOICE, speed=settings.SPEED / settings.PITCH, lang=self.lang)
        if cache:
            settings.VOICE_CACHE.mkdir(exist_ok=True)
            np.save(cache_file, samples)
        return samples

    def play(self, audio: np.ndarray) -> None:
        # Waits for the previous sound to end, then starts this one WITHOUT waiting for it,
        # so the program can prepare the next sentence or move the robot while Reachy talks.
        self.wait()
        sd.play(audio, self.play_rate)

    def wait(self) -> None:
        # Waits until Reachy has finished talking
        sd.wait()

    def say(self, text: str) -> None:
        # Prepares, plays and waits: the simple way to make Reachy say a fixed phrase
        print(f"Reachy: {text}")
        self.play(self.prepare(text, cache=True))
        self.wait()
