from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
import secrets

from src.backend.globals import DB_MANAGER, PEPPER, SESSION_STORE, AccountInfo, UserType
from src.backend.routers.utils import get_current_session
from src.backend.routers.utils import hash_password
from src.database.record_updating import update_account
from src.database.record_retrieval import get_account

# from src.database.record_retrieval import get_account_by_username, get_contact

router = APIRouter()


class UsernameUpdateRequest(BaseModel):
    username: str = Field(..., max_length=150)


@router.patch(
    "/username",
    tags=["Account"],
    summary="Change your account username",
    description="Update the username for the authenticated user. Fails if the username is taken.",
    response_model=dict,
)
async def change_username(
    data: UsernameUpdateRequest, session: tuple[str, AccountInfo] = Depends(get_current_session)
) -> dict[str, bool]:
    """
    Change the current user's username.

    Args:
        data (UsernameUpdateRequest): Contains the 'username' field.
        session (tuple): Session information from get_current_session.

    Returns:
        dict: {"success": True} if the username was updated successfully.

    Raises:
        HTTPException 409: If the requested username is already taken.
        HTTPException 400: If the update operation fails for other reasons.
    """
    account_id = session[1]["account_id"]

    async with DB_MANAGER.session() as db_session:
        updated_account = await update_account(
            session=db_session,
            id=account_id,
            username=data.username,
            commit=True,
        )

    """
    if __ contains "IntegrityError":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken."
        )
    """

    if updated_account is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update username."
        )

    return {"success": True}


class PasswordUpdateRequest(BaseModel):
    password: str = Field(..., min_length=8, max_length=128)


@router.patch(
    "/password",
    tags=["Account"],
    summary="Change your account password",
    description="Updates the password for the authenticated account. Requires a strong password.",
    response_model=dict,
)
async def change_password(
    data: PasswordUpdateRequest, session: tuple[str, dict] = Depends(get_current_session)
) -> dict:
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
        session (tuple): Session information from get_current_session.

    Returns:
        dict: {"success": True} if the password was updated successfully.

    Raises:
        HTTPException 500: If the password update operation fails.
    """
    account_id = session[1]["account_id"]
    salt = secrets.token_bytes(16)
    hashed_pw = hash_password(data.password, salt, PEPPER)

    async with DB_MANAGER.session() as db_session:
        updated_account = await update_account(
            session=db_session,
            id=account_id,
            password=hashed_pw,
            salt=salt,
            commit=True,
        )

    if updated_account is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password.",
        )

    return {"success": True}


class UpdateUserTypeRequest(BaseModel):
    user_type: UserType


@router.put(
    "/user_type",
    response_model=dict,
    tags=["Account"],
    summary="Set user type for an account.",
    description=(
        "Sets the user_type for an existing account. User type must be one of: Employer, Student, or Faculty. "
        "Cannot be changed by the user once set (contact support to change)."
    ),
)
async def set_user_type(
    data: UpdateUserTypeRequest, session: tuple[str, AccountInfo] = Depends(get_current_session)
) -> dict[str, bool]:
    """
    Set the user_type for an existing account.

    Args:
        data (UpdateUserTypeRequest): Contains new `user_type` ("Employer", "Student", "Faculty").
        session (tuple): Session information from get_current_session.

    Returns:
        dict: {"success": True} if the user_type update succeeded.

    Raises:
        HTTPException (400): If user_type is invalid or already set.
    """
    session_id, session_data = session
    account_id = session_data["account_id"]

    async with DB_MANAGER.session() as session:
        account = await get_account(session, account_id)

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        if account.user_type:
            raise HTTPException(
                status_code=409, detail="User type already set. Contact support to change."
            )

        result = await update_account(
            session=session, id=account_id, user_type=data.user_type.value, commit=True
        )

        if not result:
            raise HTTPException(
                status_code=500, detail="Failed to update user type due to server/database error."
            )

    SESSION_STORE[session_id]["user_type"] = data.user_type
    return {"success": True}


"""
class ForgotPWRequest(BaseModel):
    username: str


@router.post("/forgot-password")
async def forgot_password(data: ForgotPWRequest) -> dict:
    "
    Initiates forgot password flow. Always sends a generic success response, never reveals if user/email exists for privacy reasons.
    "
    # Lookup account
    account = await get_account_by_username(data.username)
    if account:
        # Lookup contact info
        contact = await get_contact(account.id)
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
    new_password: str


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
