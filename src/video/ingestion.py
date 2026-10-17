"""Read an MP4 frame by frame and write a video-only MP4 copy."""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from pathlib import Path

import cv2


class VideoIngestionError(Exception):
    """Raised when an input video cannot be ingested or copied."""


@dataclass(frozen=True)
class VideoInfo:
    """Metadata measured while reading a video."""

    width: int
    height: int
    fps: float
    frame_count: int
    duration_seconds: float


@dataclass(frozen=True)
class IngestionResult:
    """Metadata and output path returned by :func:`ingest_video`."""

    info: VideoInfo
    output_path: Path


def ingest_video(
    input_path: str | Path,
    output_dir: str | Path = "outputs",
) -> IngestionResult:
    """Decode every frame from an MP4 and write a copy with matching size/FPS.

    The output is encoded with OpenCV's ``mp4v`` codec. Audio is not copied.
    """
    source = Path(input_path).expanduser()
    if not source.exists():
        raise VideoIngestionError(f"Input video does not exist: {source}")
    if not source.is_file():
        raise VideoIngestionError(f"Input path is not a file: {source}")
    if source.suffix.lower() != ".mp4":
        raise VideoIngestionError(f"Input video must be an MP4 file: {source}")

    try:
        capture = cv2.VideoCapture(str(source))
    except cv2.error as exc:
        raise VideoIngestionError(f"Could not open input video: {source}") from exc

    output_directory = Path(output_dir).expanduser()
    output_path = output_directory / f"{source.stem}_copy.mp4"
    temporary_path: Path | None = None
    writer: cv2.VideoWriter | None = None
    completed = False

    try:
        if not capture.isOpened():
            raise VideoIngestionError(f"Could not open input video: {source}")

        width = int(round(capture.get(cv2.CAP_PROP_FRAME_WIDTH)))
        height = int(round(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        if width <= 0 or height <= 0:
            raise VideoIngestionError(f"Input video has invalid resolution: {source}")
        if not math.isfinite(fps) or fps <= 0:
            raise VideoIngestionError(f"Input video has invalid FPS metadata: {source}")

        output_directory.mkdir(parents=True, exist_ok=True)
        temporary_path = output_directory / f".{source.stem}.{uuid.uuid4().hex}.tmp.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(temporary_path), fourcc, fps, (width, height))
        if not writer.isOpened():
            raise VideoIngestionError(
                f"Could not create output video in directory: {output_directory}"
            )

        frame_count = 0
        while True:
            has_frame, frame = capture.read()
            if not has_frame:
                break
            if frame is None:
                raise VideoIngestionError(f"Could not decode a frame from: {source}")
            if frame.shape[1] != width or frame.shape[0] != height:
                raise VideoIngestionError(
                    f"Decoded frame resolution changed while reading: {source}"
                )

            writer.write(frame)
            frame_count += 1

        if frame_count == 0:
            raise VideoIngestionError(f"Input video contains no readable frames: {source}")

        writer.release()
        writer = None
        temporary_path.replace(output_path)
        completed = True

        info = VideoInfo(
            width=width,
            height=height,
            fps=fps,
            frame_count=frame_count,
            duration_seconds=frame_count / fps,
        )
        return IngestionResult(info=info, output_path=output_path)
    except VideoIngestionError:
        raise
    except (OSError, cv2.error) as exc:
        raise VideoIngestionError(f"Failed to ingest video {source}: {exc}") from exc
    finally:
        if writer is not None:
            writer.release()
        capture.release()
        if not completed and temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
