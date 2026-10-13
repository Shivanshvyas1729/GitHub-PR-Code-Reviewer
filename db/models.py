
import uuid
from sqlalchemy import (
    BigInteger,
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    TIMESTAMP,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    repo_full_name = Column(Text, nullable=False)
    pr_number = Column(Integer, nullable=False)
    head_sha = Column(Text, nullable=False)
    installation_id = Column(BigInteger, nullable=False)
    status = Column(Text, nullable=False, default="pending")

    created_at = Column(
        TIMESTAMP(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )



class Findings(Base):

    __tablename__ = "findings"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    pr_id = Column(UUID(as_uuid=True), ForeignKey("pull_requests.id"))

    file = Column(Text,nullable=False)

    line = Column(Integer,nullable=False)

    severity = Column(Text,nullable=False)

    message = Column(Text,nullable=False)

    agent = Column(Text,nullable=False)
    
    created_at = Column(
        TIMESTAMP(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )


class Pattern(Base):
    __tablename__ = "patterns"


    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


    repo_full_name  = Column(Text,nullable=False)

    pattern_text = Column(Text, nullable=False)
    agent = Column(Text, nullable=False)
    frequency = Column(Integer, default=1, nullable=False)

    updated_at = Column(
        TIMESTAMP(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("repo_full_name", "pattern_text", name="uq_repo_pattern"),
    )


# • __table_args__: This is a special, built-in SQLAlchemy variable. It is used to pass database-level configurations—like constraints, indexes, or specific database engine types—directly to the underlying table creation schema.
# • UniqueConstraint(...): This creates the actual restriction rules in the database.
# • "repo_full_name", "pattern_text": These are the target columns. Individually, these columns can have duplicate values. However, their combined pair must be unique.