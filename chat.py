# chat.py — Free conversation with Reachy Mini.
# Whisper hears you, Ollama (local AI) writes the replies, Kokoro speaks them, and Reachy moves to match the mood.

import json
import re
import time
import urllib.error
import urllib.request
from reachy_mini import ReachyMini

from reachy_chat.settings import (
    INPUT_MODE, MODEL, MOOD_NAMES,
    OLLAMA_URL, PATIENCE_SECONDS, SILENCE_SECONDS, SYSTEM_PROMPT, WAIT_PHRASE,
)
from reachy_chat.body import Body
from reachy_chat.ears import Ears
from reachy_chat.voice import Voice
from reachy_chat.words import asked_for_mood, turn_state, wants_to_quit


# ---------------------- Voice (Kokoro) ----------------------

voice = Voice()
wait_sound = voice.prepare(WAIT_PHRASE, cache=True)  # "Take your time, I'm listening."


# ---------------------- Ears (Whisper) ----------------------

ears = Ears() if INPUT_MODE == "voice" else None


def listen_for_turn(body: Body) -> tuple[str, float, float]:
    # Keeps listening until you've finished your thought, so "Hmm... let me think" doesn't get cut off.
    # Returns what you said, when you stopped talking, and how long Whisper took to understand it.
    parts: list[str] = []
    stopped_at = heard_seconds = 0.0
    said_wait_phrase = False
    print("(listening... talk now)")

    while True:
        audio = ears.record(give_up_after=PATIENCE_SECONDS if parts else None)
        stopped_at = time.perf_counter()
        if audio is None:  # You went quiet for a long time after "hmm", so answer what we have
            break
        text = ears.transcribe(audio)
        heard_seconds = time.perf_counter() - stopped_at
        if not text:
            continue
        parts.append(text)
        print(f"You: {text}")

        state = turn_state(" ".join(parts))
        if state == "done":
            break
        if state == "thinking" and not said_wait_phrase:
            print(f"Reachy: {WAIT_PHRASE}")
            voice.play(wait_sound)
            said_wait_phrase = True
        body.gesture("nod")  # Small nod: "I'm still here, go on"
        print("(Reachy is waiting for you to finish...)")

    return " ".join(parts), stopped_at, heard_seconds


# ---------------------- Brain (Ollama) ----------------------

def ollama_request(body: dict) -> urllib.request.Request:
    return urllib.request.Request(OLLAMA_URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})


def warm_up_ollama() -> None:
    # Loads the model now and keeps it in memory for 30 min, so the first reply isn't slow
    try:
        urllib.request.urlopen(ollama_request({"model": MODEL, "messages": [], "keep_alive": "30m"}), timeout=120).read()
    except urllib.error.URLError:
        pass  # The main loop explains the problem if Ollama is really missing


def reply_sentences(messages: list[dict]):
    # Streams the reply from Ollama and yields it one sentence at a time, as soon as each sentence is complete.
    # Sends the whole conversation each time, so the model remembers earlier messages.
    body = {"model": MODEL, "messages": messages, "stream": True, "keep_alive": "30m"}
    buffer = ""
    with urllib.request.urlopen(ollama_request(body), timeout=120) as response:
        for line in response:
            buffer += json.loads(line).get("message", {}).get("content", "")
            buffer = re.sub(r"\*[^*]*\*", " ", buffer)  # Drop finished *stage directions*
            # An unfinished *stage direction... may still be coming: only split the text before it
            star = buffer.find("*")
            ready, held = (buffer, "") if star < 0 else (buffer[:star], buffer[star:])
            *sentences, rest = re.split(r"(?<=[.!?])\s+", ready)
            buffer = rest + held
            yield from (s for s in sentences if clean_for_speech(s))
    buffer = buffer.split("*")[0]  # A *stage direction that never closed: drop it
    if clean_for_speech(buffer):
        yield buffer.strip()


def clean_for_speech(text: str) -> str:
    # Removes things that shouldn't be read aloud: *actions*, (actions), stray * and extra spaces.
    # Keeps a leading [mood] tag, which split_mood() reads.
    text = re.sub(r"\*[^*]*\*|\([^)]*\)|\*", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def split_mood(reply: str) -> tuple[str, str]:
    # "[happy] Hi there!" -> ("happy", "Hi there!"); unknown or missing tag -> "neutral"
    match = re.match(r"\s*\[(\w+)\]\s*", reply)
    if match and match.group(1).lower() in MOOD_NAMES:
        return match.group(1).lower(), reply[match.end():].strip()
    return "neutral", re.sub(r"\[\w+\]", "", reply).strip()


# ---------------------- Main ----------------------

warm_up_ollama()

messages = [{"role": "system", "content": SYSTEM_PROMPT}]  # Conversation history

with ReachyMini() as mini, Body(mini, voice) as body:
    body.set_pose("happy")
    if ears:
        ears.measure_noise()
    voice.say("Hi! I'm Reachy. Let's chat. Say bye whenever you want to stop.")

    while True:
        body.set_pose("listening")  # Leans in: "I'm listening"
        if ears:
            user_text, stopped_at, heard_seconds = listen_for_turn(body)
        else:
            user_text, stopped_at, heard_seconds = input("You: ").strip(), time.perf_counter(), 0.0
        if not user_text:
            continue

        messages.append({"role": "user", "content": user_text})
        body.set_pose("thinking")

        reply_parts, voice_seconds, brain_seconds, first_sound_at = [], [], 0.0, 0.0
        brain_started = time.perf_counter()
        try:
            for i, sentence in enumerate(reply_sentences(messages)):
                if i == 0:
                    brain_seconds = time.perf_counter() - brain_started
                reply_parts.append(sentence)
                mood, text = split_mood(sentence) if i == 0 else (None, sentence)
                if mood == "neutral" and asked_for_mood(user_text):  # "Show me a happy face" but the AI forgot the tag
                    mood = asked_for_mood(user_text)
                text = clean_for_speech(re.sub(r"\[\w+\]", " ", text))  # No actions or stray [tags] out loud
                if not text:  # Nothing to say (e.g. only "[sad] *droops*"), but still show the mood
                    if mood:
                        body.set_pose(mood)
                    continue
                print(f"Reachy: {text}")
                voice_started = time.perf_counter()
                audio = voice.prepare(text)
                voice_seconds.append(time.perf_counter() - voice_started)
                voice.play(audio)  # Starts talking...
                first_sound_at = first_sound_at or time.perf_counter()
                if mood:
                    body.set_pose(mood)  # ...and moves to the mood pose at the same time
        except urllib.error.HTTPError as error:  # Ollama replied with an error (e.g. model missing)
            print(f"Ollama error: {json.loads(error.read()).get('error', error)}")
            print(f"Tip: download the model with `ollama pull {MODEL}`")
            voice.say("Hmm, my brain gave me an error. Check the terminal.")
            break
        except urllib.error.URLError:  # Couldn't connect at all
            voice.say("Hmm, I can't reach my brain. Is Ollama running?")
            break

        voice.wait()  # Let Reachy finish the last sentence
        messages.append({"role": "assistant", "content": " ".join(reply_parts)})

        # Shows where the waiting time goes (the SILENCE_SECONDS pause before this is not included)
        if first_sound_at:
            print(
                f"   [timing] understand {heard_seconds:.2f}s | brain {brain_seconds:.2f}s | "
                f"voice {', '.join(f'{v:.2f}s' for v in voice_seconds)} | "
                f"Reachy started talking {first_sound_at - stopped_at:.2f}s after you stopped "
                f"(+{SILENCE_SECONDS}s pause to be sure you were done)"
            )

        if wants_to_quit(user_text):
            break

    # Leaving the `with` block makes Body go back to neutral and stop
