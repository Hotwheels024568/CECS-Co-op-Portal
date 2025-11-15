from datetime import datetime

SEMESTER_ORDER = ["Winter", "Summer", "Fall"]


def get_current_semester_and_year(dt: datetime) -> tuple[str, int]:
    month = dt.month
    year = dt.year
    if 1 <= month <= 4:
        return "Winter", year
    elif 5 <= month <= 8:
        return "Summer", year
    else:
        return "Fall", year


def semesters_completed(
    start_semester: str, start_year: int, current_semester: str, current_year: int
) -> int:
    sem_index = SEMESTER_ORDER.index(start_semester)
    current_index = SEMESTER_ORDER.index(current_semester)
    year, count = start_year, 0
    while (year < current_year) or (year == current_year and sem_index < current_index):
        count += 1
        sem_index += 1
        if sem_index == 3:
            sem_index = 0
            year += 1
    return count


def semesters_since_enrollment(start_semester: str, start_year: int) -> int:
    current_semester, current_year = get_current_semester_and_year(datetime.now())
    return semesters_completed(start_semester, start_year, current_semester, current_year)
