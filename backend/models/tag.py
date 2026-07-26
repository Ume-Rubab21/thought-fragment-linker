import uuid

from sqlalchemy import Column, String, ForeignKey, UniqueConstraint, Table
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (
        # Same tag name can exist for different users, but never
        # twice for the same user — this is what "normalized
        # lowercase" protects against (no "Ai" and "ai" as two tags).
        UniqueConstraint("user_id", "name", name="uq_tag_user_name"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)


# Many-to-many join table between notes and tags. No extra columns
# needed, so a plain Table (not a full model class) is enough.
note_tags = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", UUID(as_uuid=True), ForeignKey("notes.id"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id"), primary_key=True),
)