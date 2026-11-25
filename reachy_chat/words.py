# words.py — Understanding what you said: do you want to stop? Are you still thinking?

import re

from . import settings


def words_of(text: str) -> list[str]:
    # "Bye, Reachy!" -> ["bye", "reachy"]  (lowercase, no punctuation)
    return re.findall(r"[a-z']+", text.lower())


def wants_to_quit(text: str) -> bool:
    words = words_of(text)
    said_goodbye = any(word in settings.GOODBYE_WORDS for word in words)
    said_only_stop = len(words) == 1 and words[0] in settings.QUIT_WORDS
    return said_goodbye or said_only_stop


def asked_for_mood(text: str) -> str | None:
    # "Show me a sad face" -> "sad". Lets Reachy show the face even if the AI forgets the mood tag.
    words = words_of(text)
    if not any(word in ("show", "make", "face", "look", "do") for word in words):
        return None
    for word in words:
        mood = settings.MOOD_WORDS.get(word, word)
        if mood in settings.MOOD_NAMES and mood != "neutral":
            return mood
    return None


def turn_state(text: str) -> str:
    # "thinking"   = you asked for time ("Hmm.", "Let me think.")
    # "unfinished" = you stopped in the middle of a sentence ("...pizza and")
    # "done"       = Reachy can answer
    words = words_of(text)
    if not words:
        return "done"
    joined = " ".join(words)
    if all(word in settings.FILLERS for word in words):
        return "thinking"
    if any(joined == phrase or joined.endswith(" " + phrase) for phrase in settings.THINKING_PHRASES):
        return "thinking"
    if text.rstrip().endswith(("?", "!")):  # A question or exclamation is a finished sentence
        return "done"
    if words[-1] in settings.UNFINISHED_ENDINGS or text.rstrip().endswith(("...", ",", "-")):
        return "unfinished"
    return "done"
