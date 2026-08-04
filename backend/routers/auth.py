from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas.user import UserRegister, UserLogin, UserResponse, Token
from schemas.auth_extra import DirectPasswordReset
from core.security import hash_password, verify_password, create_access_token
from core.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class DeleteAccountRequest(BaseModel):
    password: str
    confirmation: str



@router.post("/register", response_model=UserResponse)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user_id=str(user.id))
    return Token(access_token=token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/password-reset/direct")
def reset_password_direct(
    payload: DirectPasswordReset,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="No account was found for this email.")

    user.password_hash = hash_password(payload.new_password)
    db.commit()

    return {"message": "Password updated successfully."}

@router.delete("/account")
def delete_account(
    payload: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Permanently delete the authenticated account and all owned data.

    The current password and the exact confirmation word DELETE are required.
    Optional tables are checked before deletion so older local databases do
    not fail when a newer migration has not yet been applied.
    """
    if payload.confirmation.strip() != "DELETE":
        raise HTTPException(
            status_code=400,
            detail="Type DELETE exactly to confirm account deletion.",
        )

    if not verify_password(payload.password, current_user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="The password you entered is incorrect.",
        )

    user_id = current_user.id

    try:
        inspector = inspect(db.get_bind())
        existing_tables = set(inspector.get_table_names())

        def table_has_columns(table_name: str, *column_names: str) -> bool:
            if table_name not in existing_tables:
                return False

            available_columns = {
                column["name"]
                for column in inspector.get_columns(table_name)
            }
            return all(name in available_columns for name in column_names)

        # Delete note-tag joins first because this older table does not use
        # ON DELETE CASCADE in every database created by the project.
        if (
            table_has_columns("note_tags", "note_id", "tag_id")
            and table_has_columns("notes", "id", "user_id")
            and table_has_columns("tags", "id", "user_id")
        ):
            db.execute(
                text(
                    """
                    DELETE FROM note_tags
                    WHERE note_id IN (
                        SELECT id FROM notes WHERE user_id = :user_id
                    )
                    OR tag_id IN (
                        SELECT id FROM tags WHERE user_id = :user_id
                    )
                    """
                ),
                {"user_id": user_id},
            )

        # Delete tables that directly belong to the user. Each table is
        # optional because local and production databases may be on
        # different migration versions.
        user_owned_tables = (
            "note_links",
            "ai_suggestions",
            "model_calls",
            "guardrail_events",
            "password_reset_tokens",
        )

        for table_name in user_owned_tables:
            if table_has_columns(table_name, "user_id"):
                db.execute(
                    text(
                        f'DELETE FROM "{table_name}" '
                        "WHERE user_id = :user_id"
                    ),
                    {"user_id": user_id},
                )

        # Embeddings reference notes instead of users.
        if (
            table_has_columns("note_embeddings", "note_id")
            and table_has_columns("notes", "id", "user_id")
        ):
            db.execute(
                text(
                    """
                    DELETE FROM note_embeddings
                    WHERE note_id IN (
                        SELECT id FROM notes WHERE user_id = :user_id
                    )
                    """
                ),
                {"user_id": user_id},
            )

        # Brain Dump-dependent rows have already been removed above.
        if table_has_columns("braindumps", "user_id"):
            db.execute(
                text(
                    "DELETE FROM braindumps "
                    "WHERE user_id = :user_id"
                ),
                {"user_id": user_id},
            )

        # Notes must be removed before collections because notes may reference
        # collection_id without ON DELETE CASCADE.
        for table_name in ("notes", "tags", "collections"):
            if table_has_columns(table_name, "user_id"):
                db.execute(
                    text(
                        f'DELETE FROM "{table_name}" '
                        "WHERE user_id = :user_id"
                    ),
                    {"user_id": user_id},
                )

        # Delete the user last.
        db.execute(
            text("DELETE FROM users WHERE id = :user_id"),
            {"user_id": user_id},
        )

        db.commit()

    except HTTPException:
        db.rollback()
        raise
    except Exception as error:
        db.rollback()
        print(
            "Account deletion failed:",
            type(error).__name__,
            str(error),
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "The account could not be deleted because the database "
                "rejected one of the cleanup operations. Check the backend "
                "terminal for the exact table or constraint error."
            ),
        ) from error

    return {
        "message": "Your ThoughtLinker account was permanently deleted."
    }
