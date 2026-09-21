from __future__ import annotations

import re
from collections import Counter

from .models import StudentRecord


def validate_records(records: list[StudentRecord]) -> None:
    for record in records:
        notes: list[str] = []
        critical_notes: list[str] = []
        if not record.name:
            critical_notes.append("姓名缺失")
        elif not re.fullmatch(r"[\u4e00-\u9fff·]{2,8}", record.name):
            critical_notes.append("姓名格式异常")

        if not record.student_id:
            critical_notes.append("学号缺失")
        elif not re.fullmatch(r"\d{8,24}", record.student_id):
            critical_notes.append("学号格式异常")

        if not record.seat_number:
            notes.append("座位号缺失")
        elif not re.fullmatch(r"\d{1,3}", record.seat_number):
            critical_notes.append("座位号格式异常")

        if record.confidence < 0.60:
            critical_notes.append("OCR置信度较低")
        notes.extend(critical_notes)
        record.notes.extend(note for note in notes if note not in record.notes)
        # The requested output fields are name and student ID. Seat number is
        # useful metadata, but some photos blur or crop only that label.
        record.status = "正常" if not critical_notes else "待复核"

    counts = Counter(
        record.student_id
        for record in records
        if record.student_id and re.fullmatch(r"\d{8,24}", record.student_id)
    )
    for record in records:
        if record.student_id and counts[record.student_id] > 1:
            if "学号重复" not in record.notes:
                record.notes.append("学号重复")
            record.status = "待复核"
