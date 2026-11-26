# reachy_chat — the parts that make Reachy Mini chat. chat.py puts them together (and holds the Ollama brain code).
#
#   settings.py  Everything you might want to change (voice, personality, poses, timings)
#   words.py     Understanding what you said: goodbye? "hmm"? unfinished sentence?
#   voice.py     Voice: turns text into speech (Kokoro) and plays it
#   ears.py      Ears: records your voice and turns it into text (Whisper)
#   body.py      Body: moves Reachy's head and antennas
