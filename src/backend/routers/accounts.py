from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, StringConstraints
from typing import Annotated
import secrets

from src.backend.globals import DB_MANAGER, SESSION_STORE, AccountInfo, UserType
from src.backend.routers.models import GeneralRequestResponse
from src.backend.routers.utils import get_current_session
from src.backend.routers.utils import hash_password
from src.database.record_updating import update_account
from src.database.record_retrieval import get_account_by_id

router = APIRouter()


class UsernameUpdateRequest(BaseModel):
    username: Annotated[str, StringConstraints(max_length=150)]


@router.patch(
    "/username",
    tags=["Account"],
    summary="Change your account username",
    description="Update the username for the authenticated user. Fails if the username is already taken.",
    response_model=GeneralRequestResponse,
)
async def change_username(
    data: UsernameUpdateRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    Change the current user's username.

    Args:
        data (UsernameUpdateRequest): Contains the 'username' field.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: {"success": True, "message": "Username changed"} if the username was updated successfully.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (409): If the requested username is already taken.
        HTTPException (500): If the operation fails.
    """
    account_id = session_data[1]["account_id"]

    async with DB_MANAGER.session() as db_session:
        result = await update_account(
            db_session,
            account_id,
            data.username,
            commit=True,
        )

    """
    if __ contains "IntegrityError":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken."
        )
    """

    if result is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to update username.")

    return GeneralRequestResponse(success=True, message="Username changed")


class PasswordUpdateRequest(BaseModel):
    password: Annotated[str, StringConstraints(min_length=8, max_length=128)]


@router.patch(
    "/password",
    tags=["Account"],
    summary="Change your account password",
    description="Updates the password for the authenticated account.",
    response_model=GeneralRequestResponse,
)
async def change_password(
    data: PasswordUpdateRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    Change the current user's password.

    For stronger security, consider adding additional password strength checks using the zxcvbn library.

        from zxcvbn import zxcvbn
        if zxcvbn(data.password)['score'] < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password too weak. Please choose a stronger password."
            )

    Args:
        data (PasswordUpdateRequest): Contains the 'password' field.
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: {"success": True, "message": "Password changed"} if the password was updated successfully.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (500): If the operation fails.
    """
    account_id = session_data[1]["account_id"]
    salt = secrets.token_bytes(16)
    hashed_pw = hash_password(data.password, salt)

    async with DB_MANAGER.session() as db_session:
        result = await update_account(
            db_session,
            account_id,
            hashed_pw,
            salt,
            commit=True,
        )

    if result is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to update password.")

    return GeneralRequestResponse(success=True, message="Password changed")


class UpdateUserTypeRequest(BaseModel):
    user_type: UserType


@router.put(
    "/user_type",
    tags=["Account"],
    summary="Set user type for an account.",
    description=(
        "Sets the user_type for an existing account. User type must be one of: Employer, Student, or Faculty. "
        "Cannot be changed by the user once set (contact support to change)."
    ),
    response_model=GeneralRequestResponse,
)
async def set_user_type(
    data: UpdateUserTypeRequest,
    session_data: tuple[str, AccountInfo] = Depends(get_current_session),
) -> GeneralRequestResponse:
    """
    Set the user_type for an existing account.

    Args:
        data (UpdateUserTypeRequest): Contains new `user_type` ("Employer", "Student", "Faculty").
        session_data (tuple[str, AccountInfo], optional): Session information from get_current_session.

    Returns:
        GeneralRequestResponse: {"success": True, "message": "User type set"} if the user_type update succeeded.

    Raises:
        HTTPException (401): If the session is invalid or expired.
        HTTPException (404): If the account is not found.
        HTTPException (409): If user_type is already set.
        HTTPException (500): If the operation fails.
    """
    session_id = session_data[0]
    account_id = session_data[1]["account_id"]

    async with DB_MANAGER.session() as db_session:
        account = await get_account_by_id(db_session, account_id)

        if not account:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Account not found")

        if account.user_type is not None:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "User type already set. Contact support to change."
            )

        result = await update_account(
            db_session, account_id, user_type=data.user_type.value, commit=True
        )

        if not result:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Failed to update user type due to server/database error.",
            )

    SESSION_STORE[session_id]["user_type"] = data.user_type
    return GeneralRequestResponse(success=True, message="User type set")


"""
from src.database.record_retrieval import get_account_by_username

class ForgotPWRequest(BaseModel):
    username: Annotated[str, StringConstraints(max_length=150)]


@router.post("/forgot-password")
async def forgot_password(data: ForgotPWRequest) -> dict:
    "
    Initiates forgot password flow. Always sends a generic success response, never reveals if user/email exists for privacy reasons.
    "
    # Lookup account
    account = await get_account_by_username(data.username)
    if account:
        # Lookup contact info
        contact = account.contact
        if contact and contact.email:
            reset_token = await create_password_reset_token(account.id)
            await send_password_reset_email(contact.email, reset_token)
            # Log the event, rate limit if desired
    # Always respond generically
    return {
        "success": True,
        "message": "If this account exists, a password reset email has been sent.",
    }


class CompleteResetRequest(BaseModel):
    token: str
    new_password: Annotated[str, StringConstraints(min_length=8, max_length=128)]


@router.post("/reset-password")
async def reset_password(data: CompleteResetRequest) -> dict:
    "
    Completes password reset given a valid token and new password.
    "
    # Validate token existence and expiration
    account_id = await get_account_id_from_token(data.token)
    if not account_id:
        raise HTTPException(400, "Invalid or expired token.")
    # Update password with new salt and hash
    salt = secrets.token_bytes(16)
    pw_hash = hash_password(data.new_password, salt, PEPPER)
    async with DB_MANAGER.session() as session:
        updated = await update_account(
            session, id=account_id, password=pw_hash, salt=salt, commit=True
        )
        if not updated:
            raise HTTPException(500, "Password reset failed.")
        await invalidate_password_reset_token(data.token)
    return {"success": True}


You may want a password_reset_tokens table:
    class PasswordResetToken(Base):
        __tablename__ = "password_reset_tokens"
        id = mapped_column(primary_key=True)
        account_id = mapped_column(ForeignKey("accounts.id"), nullable=False)
        token = mapped_column(String(64), unique=True, nullable=False)
        expires_at = mapped_column(TIMESTAMP, nullable=False) # Typically 1 hour
"""
