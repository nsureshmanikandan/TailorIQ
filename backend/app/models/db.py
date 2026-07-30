"""SQLAlchemy ORM models matching the PostgreSQL schema.

All models use UUID primary keys with server-side default generation via
gen_random_uuid(). Relationships are defined with appropriate cascading
delete behavior to maintain referential integrity.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class User(Base):
    """User account supporting email/password and OAuth authentication."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    oauth_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    oauth_provider_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    # Relationships
    resumes: Mapped[list["Resume"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    resume_versions: Mapped[list["ResumeVersion"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    job_descriptions: Mapped[list["JobDescription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    match_results: Mapped[list["MatchResult"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Resume(Base):
    """Uploaded or pasted resume content with optional blob storage reference."""

    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    original_filename: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    file_format: Mapped[str] = mapped_column(String(10), nullable=False)
    blob_storage_path: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="resumes")
    versions: Mapped[list["ResumeVersion"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan"
    )
    match_results: Mapped[list["MatchResult"]] = relationship(
        back_populates="resume"
    )


class ResumeVersion(Base):
    """Named resume version slot (max 3 per user: fresher, experienced, domain-specific)."""

    __tablename__ = "resume_versions"
    __table_args__ = (
        UniqueConstraint("user_id", "label", name="uq_resume_versions_user_label"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="resume_versions")
    resume: Mapped["Resume"] = relationship(back_populates="versions")


class JobDescription(Base):
    """Job description input from text paste or URL fetch."""

    __tablename__ = "job_descriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_type: Mapped[str] = mapped_column(String(10), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="job_descriptions")
    match_results: Mapped[list["MatchResult"]] = relationship(
        back_populates="job_description"
    )


class MatchResult(Base):
    """Complete analysis run results with all agent outputs stored as JSONB."""

    __tablename__ = "match_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id"),
        nullable=False,
    )
    jd_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_descriptions.id"),
        nullable=False,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'pending'")
    )

    # Agent output JSONB columns
    pass1_score: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    pass2_score: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    gap_report: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ats_report: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    parsed_resume: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    parsed_jd: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    tailored_resume: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    verification_report: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    cover_letter: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    interview_guide: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Metrics
    total_tokens_used: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    total_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(6, 4), server_default=text("0.0")
    )

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="match_results")
    resume: Mapped["Resume"] = relationship(back_populates="match_results")
    job_description: Mapped["JobDescription"] = relationship(
        back_populates="match_results"
    )
    generated_artifacts: Mapped[list["GeneratedArtifact"]] = relationship(
        back_populates="match_result", cascade="all, delete-orphan"
    )


class GeneratedArtifact(Base):
    """Downloadable file artifact produced by the package generation agent."""

    __tablename__ = "generated_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    match_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("match_results.id", ondelete="CASCADE"),
        nullable=False,
    )
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False)
    blob_storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    # Relationships
    match_result: Mapped["MatchResult"] = relationship(
        back_populates="generated_artifacts"
    )


class AuditLog(Base):
    """Audit trail for user actions and agent operations (PII-redacted)."""

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    agent_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="audit_logs")
