"""Video ingestion and processing functionality."""

from .ingestion import IngestionResult, VideoInfo, VideoIngestionError, ingest_video

__all__ = ["IngestionResult", "VideoInfo", "VideoIngestionError", "ingest_video"]
