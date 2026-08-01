import uuid
from datetime import datetime

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from core.deps import get_current_user
from database import get_db
from models.brain_dump import BrainDump
from models.user import User
from schemas.ai_suggestion_action import (
    CreatedNoteLinkResponse,
    SuggestionAcceptRequest,
    SuggestionDecisionResponse,
    SuggestionRejectRequest,
)
from schemas.day10_graph import (
    BrainDumpGapResponse,
    BrainDumpGraphResponse,
    KnowledgeGapResponse,
)
from schemas.brain_dump import (
    BrainDumpCreate,
    BrainDumpResponse,
    BrainDumpStatusResponse,
    BrainDumpSuggestionResponse,
)
from services.brain_dump_query_service import (
    BrainDumpNotFoundError,
    BrainDumpSuggestionNotFoundError,
    BrainDumpSuggestionNotReadyError,
    get_brain_dump_suggestion,
)
from services.brain_dump_graph import describe_brain_dump_graph
from services.knowledge_gap_service import detect_knowledge_gaps
from services.brain_dump_service import (
    create_brain_dump,
    process_brain_dump,
)
from services.suggestion_decision_service import (
    SuggestionDecisionConflictError,
    SuggestionDecisionNotFoundError,
    SuggestionDecisionValidationError,
    accept_suggestion,
    reject_suggestion,
)


router = APIRouter(
    prefix="/brain-dumps",
    tags=["brain-dumps"],
)


def get_owned_brain_dump_or_404(
    brain_dump_id: uuid.UUID,
    db: Session,
    current_user: User,
) -> BrainDump:
    brain_dump = (
        db.query(BrainDump)
        .filter(
            BrainDump.id == brain_dump_id,
            BrainDump.user_id == current_user.id,
        )
        .first()
    )

    if brain_dump is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brain dump not found.",
        )

    return brain_dump


@router.get(
    "/graph/inspect",
    response_model=BrainDumpGraphResponse,
)
def inspect_brain_dump_graph(
    current_user: User = Depends(get_current_user),
):
    """Return the inspectable Day 10 graph structure."""
    return BrainDumpGraphResponse(**describe_brain_dump_graph())


@router.get(
    "/{brain_dump_id}/gaps",
    response_model=BrainDumpGapResponse,
)
def get_brain_dump_gaps(
    brain_dump_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    brain_dump = get_owned_brain_dump_or_404(
        brain_dump_id=brain_dump_id,
        db=db,
        current_user=current_user,
    )
    gaps = detect_knowledge_gaps(brain_dump.raw_text)
    return BrainDumpGapResponse(
        brain_dump_id=str(brain_dump.id),
        gaps=[KnowledgeGapResponse(**gap.to_dict()) for gap in gaps],
    )


@router.post(
    "",
    response_model=BrainDumpResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def submit_brain_dump(
    payload: BrainDumpCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Store the Brain Dump immediately and process it asynchronously.
    """

    brain_dump = create_brain_dump(
        db=db,
        user_id=current_user.id,
        raw_text=payload.raw_text,
    )

    background_tasks.add_task(
        process_brain_dump,
        brain_dump.id,
    )

    return brain_dump


@router.get(
    "/{brain_dump_id}/status",
    response_model=BrainDumpStatusResponse,
)
def get_brain_dump_status(
    brain_dump_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_owned_brain_dump_or_404(
        brain_dump_id=brain_dump_id,
        db=db,
        current_user=current_user,
    )


@router.get(
    "/{brain_dump_id}/suggestion",
    response_model=BrainDumpSuggestionResponse,
)
def get_generated_brain_dump_suggestion(
    brain_dump_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        brain_dump, suggestion = get_brain_dump_suggestion(
            db=db,
            user_id=current_user.id,
            brain_dump_id=brain_dump_id,
        )

    except BrainDumpNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except BrainDumpSuggestionNotReadyError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    except BrainDumpSuggestionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return BrainDumpSuggestionResponse(
        brain_dump_id=brain_dump.id,
        brain_dump_status=brain_dump.status,
        suggestion_id=suggestion.id,
        suggested_title=suggestion.suggested_title,
        summary=suggestion.summary,
        tags=list(suggestion.tags or []),
        keywords=list(suggestion.keywords or []),
        related_note_ids=[
            str(note_id)
            for note_id in (
                suggestion.related_note_ids or []
            )
        ],
        model_name=suggestion.model_name,
        prompt_tokens=suggestion.prompt_tokens,
        completion_tokens=suggestion.completion_tokens,
        total_tokens=suggestion.total_tokens,
        attempts=suggestion.attempts,
        retry_count=suggestion.retry_count,
        suggestion_status=suggestion.status,
        created_at=suggestion.created_at,
        updated_at=suggestion.updated_at,
    )


@router.post(
    "/{brain_dump_id}/suggestion/accept",
    response_model=SuggestionDecisionResponse,
)
def accept_generated_suggestion(
    brain_dump_id: uuid.UUID,
    payload: SuggestionAcceptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accept the suggestion and create:

    - a permanent Note
    - accepted Tags
    - approved related-note links
    - a Note embedding
    """

    try:
        result = accept_suggestion(
            db=db,
            user_id=current_user.id,
            brain_dump_id=brain_dump_id,
            title=payload.title,
            body_md=payload.body_md,
            tags=payload.tags,
            selected_related_note_ids=payload.selected_related_note_ids,
        )

    except SuggestionDecisionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except SuggestionDecisionConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    except SuggestionDecisionValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    created_link_responses = [
        CreatedNoteLinkResponse(
            link_id=link.id,
            from_note_id=link.from_note_id,
            to_note_id=link.to_note_id,
            reason=link.reason,
            confidence=link.confidence,
        )
        for link in result.created_links
    ]

    return SuggestionDecisionResponse(
        suggestion_id=result.suggestion.id,
        brain_dump_id=result.suggestion.brain_dump_id,
        decision="accepted",
        suggestion_status=result.suggestion.status,
        note_id=result.note.id,
        embedding_status=(
            "ready"
            if result.embedding_ready
            else "failed"
        ),
        links_created=len(
            result.created_links
        ),
        created_links=created_link_responses,
        skipped_related_note_ids=(
            result.skipped_related_note_ids
        ),
        decided_at=(
            result.suggestion.decided_at
            or datetime.utcnow()
        ),
        message=(
            "Suggestion accepted. Note, tags, embedding, "
            "and approved related-note links were processed."
        ),
    )


@router.post(
    "/{brain_dump_id}/suggestion/reject",
    response_model=SuggestionDecisionResponse,
)
def reject_generated_suggestion(
    brain_dump_id: uuid.UUID,
    payload: SuggestionRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reject the suggestion without creating a Note or NoteLink.
    """

    try:
        suggestion = reject_suggestion(
            db=db,
            user_id=current_user.id,
            brain_dump_id=brain_dump_id,
            reason=payload.reason,
        )

    except SuggestionDecisionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except SuggestionDecisionConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    except SuggestionDecisionValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return SuggestionDecisionResponse(
        suggestion_id=suggestion.id,
        brain_dump_id=suggestion.brain_dump_id,
        decision="rejected",
        suggestion_status=suggestion.status,
        note_id=None,
        embedding_status="not-created",
        links_created=0,
        created_links=[],
        skipped_related_note_ids=[],
        decided_at=(
            suggestion.decided_at
            or datetime.utcnow()
        ),
        message=(
            "Suggestion rejected. No note or related-note "
            "link was created."
        ),
    )


@router.get(
    "/{brain_dump_id}",
    response_model=BrainDumpResponse,
)
def get_brain_dump(
    brain_dump_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_owned_brain_dump_or_404(
        brain_dump_id=brain_dump_id,
        db=db,
        current_user=current_user,
    )