from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


EMBEDDING_DIMENSIONS = 384

DEFAULT_EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)


class NoteEmbedding(Base):
    __tablename__ = "note_embeddings"

    note_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "notes.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    embedding = Column(
        Vector(EMBEDDING_DIMENSIONS),
        nullable=False,
    )

    embedding_model = Column(
        String(120),
        nullable=False,
        default=DEFAULT_EMBEDDING_MODEL,
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

    note = relationship(
        "Note",
        back_populates="embedding_record",
    )