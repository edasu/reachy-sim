# ears.py — Reachy's ears: records your voice from the microphone and turns it into text with Whisper.

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel  # Offline speech-to-text

from . import settings

RATE = settings.MIC_RATE
BLOCK_SECONDS = 0.1  # Check the microphone every 0.1 s


class Ears:
    def __init__(self):
        print("Loading Reachy's ears...")
        try:  # Apple GPU: about 3x faster than the CPU (0.5 s instead of 1.5 s), but experimental
            self.whisper = WhisperModel(settings.WHISPER_MODEL, device="mps")
        except Exception:  # Fall back to the CPU if the GPU doesn't work
            self.whisper = WhisperModel(settings.WHISPER_MODEL, device="cpu", compute_type="int8")
        self.transcribe(np.zeros(RATE, dtype=np.float32))  # Warm-up, so the first real answer is fast
        self.noise_level = 0.0
        self.hearing_you = False  # True while you're talking (Body uses it to nod along)

    def measure_noise(self) -> None:
        # Listens to the room for 1 second so we know what "silence" sounds like
        print("Measuring room noise, stay quiet for a second...")
        audio = sd.rec(RATE, samplerate=RATE, channels=1, dtype="float32")
        sd.wait()
        if not audio.any():  # Exactly zero = macOS is blocking the mic (a real room is never perfectly silent)
            raise SystemExit(
                "The microphone gives only silence, so macOS is probably blocking it.\n"
                "Fix: System Settings > Privacy & Security > Microphone > turn on the app running this script\n"
                "(Visual Studio Code or Terminal), then fully quit and reopen that app.\n"
                'Or set INPUT_MODE = "text" in reachy_chat/settings.py to type instead.'
            )
        self.noise_level = float(np.sqrt(np.mean(audio**2)))

    def record(self, give_up_after: float | None = None) -> np.ndarray | None:
        # Waits for you to start talking, then records until you've been quiet for SILENCE_SECONDS.
        # Returns None if you don't start talking within give_up_after seconds.
        sd.wait()  # Never record while Reachy is still talking, or it would hear itself
        threshold = max(self.noise_level * 3, 0.01)  # Louder than this = you're talking
        block = int(RATE * BLOCK_SECONDS)
        chunks, started, quiet_blocks, waited_blocks = [], False, 0, 0

        with sd.InputStream(samplerate=RATE, channels=1, dtype="float32", blocksize=block) as stream:
            while True:
                chunk, _ = stream.read(block)
                loud = np.sqrt(np.mean(chunk**2)) > threshold

                if not started:  # Still waiting for you to start talking
                    chunks = (chunks + [chunk])[-3:]  # Keep a little audio from just before you spoke
                    started = loud
                    waited_blocks += 1
                    if give_up_after and waited_blocks * BLOCK_SECONDS >= give_up_after:
                        return None
                    continue

                chunks.append(chunk)
                quiet_blocks = 0 if loud else quiet_blocks + 1
                self.hearing_you = quiet_blocks < 5  # Talked in the last half second
                done_talking = quiet_blocks * BLOCK_SECONDS >= settings.SILENCE_SECONDS
                too_long = len(chunks) * BLOCK_SECONDS >= settings.MAX_RECORD_SECONDS
                if done_talking or too_long:
                    self.hearing_you = False
                    return np.concatenate(chunks).flatten()

    def transcribe(self, audio: np.ndarray) -> str:
        # vad_filter drops parts with no speech; without it Whisper invents words like "You" from noise
        segments, _ = self.whisper.transcribe(audio, language="en", beam_size=1, vad_filter=True)
        return " ".join(segment.text for segment in segments).strip()
