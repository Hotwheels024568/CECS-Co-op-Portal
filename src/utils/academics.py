from datetime import datetime
from enum import Enum


class Semester(str, Enum):
    WINTER = "Winter"
    SUMMER = "Summer"
    FALL = "Fall"

    @property
    def order(self) -> int:
        return list(type(self)).index(self)

    @classmethod
    def length(cls) -> int:
        return len(cls)


SEMESTER_MONTH_RANGES = {
    Semester.WINTER: range(1, 5),
    Semester.SUMMER: range(5, 9),
    Semester.FALL: range(9, 13),
}


def get_current_semester_and_year(datetime: datetime) -> tuple[Semester, int]:
    month = datetime.month
    year = datetime.year
    if 1 <= month <= 4:
        return Semester.WINTER, year
    elif 5 <= month <= 8:
        return Semester.SUMMER, year
    else:
        return Semester.FALL, year


def get_current_semester_and_year(datetime: datetime) -> tuple[Semester, int]:
    month = datetime.month
    year = datetime.year
    for semester, months in SEMESTER_MONTH_RANGES.items():
        if month in months:
            return semester, year
    raise ValueError(f"Month {month} not mapped to any semester.")


def semesters_completed(
    start_semester: Semester, start_year: int, current_semester: Semester, current_year: int
) -> int:
    sem_index = start_semester.order
    current_index = current_semester.order
    year, count = start_year, 0
    while (year < current_year) or (year == current_year and sem_index < current_index):
        count += 1
        sem_index += 1
        if sem_index == Semester.length():
            sem_index = 0
            year += 1
    return count


def semesters_since_enrollment(start_semester: Semester, start_year: int) -> int:
    current_semester, current_year = get_current_semester_and_year(datetime.now())
    return semesters_completed(start_semester, start_year, current_semester, current_year)
