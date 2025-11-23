from typing import Annotated, Optional
from pydantic import BaseModel, StringConstraints  # , EmailStr


class GeneralRequestResponse(BaseModel):
    success: bool
    message: str


class ContactResponse(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    email: str
    phone: Optional[str] = None


class ContactCreationRequest(BaseModel):
    first_name: Annotated[str, StringConstraints(max_length=50)]
    middle_name: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    last_name: Annotated[str, StringConstraints(max_length=50)]
    email: Annotated[str, StringConstraints(max_length=254)]
    # email: Annotated[EmailStr, StringConstraints(max_length=254)]
    phone: Optional[Annotated[str, StringConstraints(max_length=50)]] = None


class ContactUpdateRequest(BaseModel):
    first_name: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    middle_name: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    last_name: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    email: Optional[Annotated[str, StringConstraints(max_length=254)]] = None
    # email: Optional[Annotated[EmailStr, StringConstraints(max_length=254)]] = None
    phone: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
