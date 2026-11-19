"""Pydantic schemas for API request validation and response serialization."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnalysisStatusResponse(BaseModel):
    """Status polling response for an analysis task."""
    id: str
    status: str
    created_at: datetime
    use_case: str
    method: str
    error: Optional[str] = None

    class Config:
        from_attributes = True


class AnalysisUrls(BaseModel):
    """Direct URL links to generated visual outputs and geodata."""
    before_preview: Optional[str] = None
    after_preview: Optional[str] = None
    diff: Optional[str] = None
    change_mask: Optional[str] = None
    overlay: Optional[str] = None
    geojson: Optional[str] = None


class AnalysisResultResponse(BaseModel):
    """Comprehensive analytical result payload."""
    id: str
    status: str
    created_at: datetime
    use_case: str
    method: str
    is_multispectral: bool
    stats: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    urls: AnalysisUrls
    error: Optional[str] = None

    class Config:
        from_attributes = True


class CompareResultResponse(BaseModel):
    """Comparative benchmarking results across DIP methods."""
    id: str
    use_case: str
    best_method: str
    metrics_table: List[Dict[str, Any]]
    method_mask_urls: Dict[str, str]
    is_multispectral: bool


class HistoryItem(BaseModel):
    """Summary record of a past analysis."""
    id: str
    created_at: datetime
    use_case: str
    method: str
    status: str
    before_name: str
    after_name: str
    percent_change: Optional[float] = None
    changed_km2: Optional[float] = None
    overlay_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    class Config:
        from_attributes = True


class UseCaseInfo(BaseModel):
    """Configuration and metadata for an environmental monitoring application."""
    id: str
    name: str
    index_name: str
    full_index_name: str
    formula: str
    accent_color: str
    target_direction: str
    description: str
