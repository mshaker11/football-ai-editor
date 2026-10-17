"""Unit tests for video ingestion without requiring a video codec."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2

from src.video.ingestion import VideoIngestionError, ingest_video


class FakeFrame:
    shape = (48, 64, 3)


class FakeCapture:
    def __init__(self, frame_count: int = 3, opened: bool = True) -> None:
        self.frames_remaining = frame_count
        self.opened = opened
        self.released = False

    def isOpened(self) -> bool:
        return self.opened

    def get(self, property_id: int) -> float:
        values = {
            cv2.CAP_PROP_FRAME_WIDTH: 64.0,
            cv2.CAP_PROP_FRAME_HEIGHT: 48.0,
            cv2.CAP_PROP_FPS: 25.0,
        }
        return values[property_id]

    def read(self) -> tuple[bool, FakeFrame | None]:
        if self.frames_remaining == 0:
            return False, None
        self.frames_remaining -= 1
        return True, FakeFrame()

    def release(self) -> None:
        self.released = True


class FakeWriter:
    def __init__(self, path: str, fps: float, size: tuple[int, int]) -> None:
        self.path = Path(path)
        self.fps = fps
        self.size = size
        self.frames: list[FakeFrame] = []

    def isOpened(self) -> bool:
        return True

    def write(self, frame: FakeFrame) -> None:
        self.frames.append(frame)

    def release(self) -> None:
        self.path.write_bytes(b"test video")


class IngestVideoTests(unittest.TestCase):
    def test_decodes_all_frames_and_writes_copy_with_source_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "match.mp4"
            source.touch()
            capture = FakeCapture(frame_count=4)
            writers: list[FakeWriter] = []

            def create_writer(path: str, _fourcc: int, fps: float, size: tuple[int, int]) -> FakeWriter:
                writer = FakeWriter(path, fps, size)
                writers.append(writer)
                return writer

            with (
                patch("src.video.ingestion.cv2.VideoCapture", return_value=capture),
                patch("src.video.ingestion.cv2.VideoWriter", side_effect=create_writer),
                patch("src.video.ingestion.cv2.VideoWriter_fourcc", return_value=1),
            ):
                result = ingest_video(source, root / "outputs")

            self.assertEqual(result.info.width, 64)
            self.assertEqual(result.info.height, 48)
            self.assertEqual(result.info.fps, 25.0)
            self.assertEqual(result.info.frame_count, 4)
            self.assertAlmostEqual(result.info.duration_seconds, 0.16)
            self.assertEqual(result.output_path, root / "outputs" / "match_copy.mp4")
            self.assertTrue(result.output_path.is_file())
            self.assertEqual(len(writers[0].frames), 4)
            self.assertEqual(writers[0].size, (64, 48))
            self.assertEqual(writers[0].fps, 25.0)
            self.assertTrue(capture.released)

    def test_invalid_input_path_has_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing.mp4"
            with self.assertRaisesRegex(VideoIngestionError, "does not exist"):
                ingest_video(missing)

    def test_rejects_non_mp4_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "match.avi"
            source.touch()
            with self.assertRaisesRegex(VideoIngestionError, "must be an MP4"):
                ingest_video(source)

    def test_rejects_video_that_cannot_be_opened(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "broken.mp4"
            source.touch()
            capture = FakeCapture(opened=False)
            with patch("src.video.ingestion.cv2.VideoCapture", return_value=capture):
                with self.assertRaisesRegex(VideoIngestionError, "Could not open"):
                    ingest_video(source)
            self.assertTrue(capture.released)


if __name__ == "__main__":
    unittest.main()
