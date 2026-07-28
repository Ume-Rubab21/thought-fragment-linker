import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    Computed,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import relationship

from database import Base
from models.tag import note_tags


SEARCH_VECTOR_SQL = """
setweight(
    to_tsvector(
        'english'::regconfig,
        coalesce(title, '')
    ),
    'A'
) ||
setweight(
    to_tsvector(
        'english'::regconfig,
        regexp_replace(
            coalesce(body_md, ''),
            '<[^>]+>',
            ' ',
            'g'
        )
    ),
    'B'
)
"""


class Note(Base):
    __tablename__ = "notes"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    title = Column(
        String(180),
        nullable=False,
    )

    body_md = Column(
        Text,
        nullable=False,
        default="",
    )

    source = Column(
        String,
        nullable=False,
        default="manual",
    )

    collection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("collections.id"),
        nullable=True,
        index=True,
    )

    search_vector = Column(
        TSVECTOR,
        Computed(
            SEARCH_VECTOR_SQL,
            persisted=True,
        ),
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    tags = relationship(
        "Tag",
        secondary=note_tags,
        backref="notes",
    )

    embedding_record = relationship(
        "NoteEmbedding",
        back_populates="note",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )