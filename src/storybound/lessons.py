"""The four lessons. Each has a one-sentence concept and terms that show the concept is on the page."""

from __future__ import annotations

from .models import Lesson

LESSONS: dict[str, Lesson] = {
    l.id: l
    for l in [
        Lesson(
            id="sharing",
            title="Sharing",
            blurb="Sharing makes good things better for everyone.",
            concept="Sharing what you have with others makes everyone happier, including you.",
            terms=["share", "sharing", "shared", "give", "half", "together", "turn", "take turns", "both"],
            icon="gift",
        ),
        Lesson(
            id="honesty",
            title="Telling the truth",
            blurb="Saying what really happened, even when it is hard.",
            concept="Telling the truth, even when it is hard, builds trust and feels better than hiding.",
            terms=["truth", "true", "honest", "tell", "told", "said", "sorry", "admit", "really happened"],
            icon="star",
        ),
        Lesson(
            id="kindness",
            title="Being kind",
            blurb="Small kind acts can change someone's whole day.",
            concept="Noticing how others feel and helping gently makes friends and makes everyone feel safe.",
            terms=["kind", "kindness", "help", "helped", "gentle", "friend", "feel", "care", "cheer"],
            icon="heart",
        ),
        Lesson(
            id="patience",
            title="Being patient",
            blurb="Good things come to those who wait and try again.",
            concept="Waiting calmly and trying again, instead of giving up or grabbing, lets good things happen.",
            terms=["wait", "waiting", "patient", "patience", "try again", "slowly", "calm", "breathe", "later"],
            icon="clock",
        ),
    ]
}


def get(lesson_id: str) -> Lesson:
    try:
        return LESSONS[lesson_id]
    except KeyError:
        raise KeyError(f"unknown lesson: {lesson_id}") from None
