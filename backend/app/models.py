"""SQLAlchemy database models for image change detection analyses."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text
from .database import Base


class Analysis(Base):
    """Stores metadata, status, configuration, and statistical results of an analysis."""
    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    use_case = Column(String(50), nullable=False)
    method = Column(String(50), nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # pending, running, done, failed
    before_name = Column(String(255), nullable=False)
    after_name = Column(String(255), nullable=False)
    is_multispectral = Column(Boolean, default=True, nullable=False)
    stats_json = Column(Text, nullable=True)  # Stores JSON serialized statistics and metrics
    output_dir = Column(String(500), nullable=True)
    error = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Analysis id={self.id} use_case={self.use_case} status={self.status}>"
