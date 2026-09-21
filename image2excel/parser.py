from __future__ import annotations

import re
import unicodedata

from .models import TextBox, text_join


SEAT_PATTERN = re.compile(r"(?:座位号|座位|座号)[ \t]*[:：]?[ \t]*(\d{1,3})")
NAME_PATTERN = re.compile(
    r"(?:姓[ \t]*名|姓名)[ \t]*[:：]?[ \t]*([\u4e00-\u9fff·]{2,8})"
)
ID_PATTERN = re.compile(r"(?:学号|学)[ \t]*[:：]?[ \t]*([0-9A-Za-z|]{8,24})")
GENERIC_ID_PATTERN = re.compile(r"(?<!\d)(20\d{8,20})(?!\d)")


def parse_student(boxes: list[TextBox]) -> tuple[dict[str, str], float, str]:
    raw_text = text_join(boxes)
    normalized = _normalize_text(raw_text)

    seat_match = SEAT_PATTERN.search(normalized)
    name_match = NAME_PATTERN.search(normalized)
    id_match = ID_PATTERN.search(normalized)
    if id_match is None:
        id_match = GENERIC_ID_PATTERN.search(normalized)

    seat_number = seat_match.group(1) if seat_match else ""
    name = name_match.group(1) if name_match else ""
    student_id = _clean_student_id(id_match.group(1)) if id_match else ""
    confidence = sum(box.score for box in boxes) / len(boxes) if boxes else 0.0
    return (
        {
            "seat_number": seat_number,
            "name": name,
            "student_id": student_id,
            "raw_text": raw_text,
        },
        confidence,
        normalized,
    )


def has_student_signal(raw_text: str) -> bool:
    normalized = _normalize_text(raw_text)
    if not normalized:
        return False
    return bool(
        SEAT_PATTERN.search(normalized)
        or NAME_PATTERN.search(normalized)
        or ID_PATTERN.search(normalized)
        or GENERIC_ID_PATTERN.search(normalized)
    )


def _normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = value.replace("\u3000", " ")
    value = value.replace("座位号", "座位号").replace("学 号", "学号")
    return value


def _clean_student_id(value: str) -> str:
    replacements = str.maketrans(
        {
            "O": "0",
            "o": "0",
            "I": "1",
            "l": "1",
            "|": "1",
        }
    )
    return re.sub(r"\D", "", value.translate(replacements))
