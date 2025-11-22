from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from src.backend.globals import DB_MANAGER, AccountInfo, UserType

router = APIRouter()

"""
Faculty
    get dept

Students
    create
    get personal
    update personal
    delete personal

Employers
    get apps to postings
    select candidates
    update status
"""


"""
coop_credit_eligibility = (
    student.gpa >= 2
    and internship.duration_weeks >= 7
    and internship.total_work_hours >= 140
    and semesters_since_enrollment(student.start_semester, student.start_year)
    >= (1 if student.transfer else 2)
)
"""
