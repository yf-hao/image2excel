from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


Point = tuple[float, float]


@dataclass(frozen=True)
class TextBox:
    text: str
    score: float
    points: tuple[Point, ...]

    @property
    def x1(self) -> float:
        return min(point[0] for point in self.points)

    @property
    def y1(self) -> float:
        return min(point[1] for point in self.points)

    @property
    def x2(self) -> float:
        return max(point[0] for point in self.points)

    @property
    def y2(self) -> float:
        return max(point[1] for point in self.points)

    @property
    def center_x(self) -> float:
        return (self.x1 + self.x2) / 2

    @property
    def center_y(self) -> float:
        return (self.y1 + self.y2) / 2


@dataclass
class StudentRecord:
    page_index: int
    source_image: str
    column: int | None
    row: int | None
    seat_number: str = ""
    name: str = ""
    student_id: str = ""
    confidence: float = 0.0
    status: str = "待复核"
    raw_text: str = ""
    orientation: int = 0
    location: tuple[int, int, int, int] | None = None
    notes: list[str] = field(default_factory=list)

    def as_row(self) -> list[object]:
        return [
            self.seat_number,
            self.student_id,
            self.name,
            "；".join(self.notes),
        ]


def text_join(boxes: Sequence[TextBox]) -> str:
    """Return OCR text in top-to-bottom, left-to-right order."""
    ordered = sorted(boxes, key=lambda item: (item.center_y, item.center_x))
    return "\n".join(item.text.strip() for item in ordered if item.text.strip())
