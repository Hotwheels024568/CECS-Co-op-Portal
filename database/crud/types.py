from typing import TypeVar

from database.schema import Base

T = TypeVar("T")
TAttr = TypeVar("TAttr")
TModel = TypeVar("TModel", bound=Base)
