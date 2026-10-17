"""Command-line entry point for Stage 1 video ingestion."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.video.ingestion import VideoIngestionError, ingest_video


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read an MP4 video and write a video-only copy to outputs/."
    )
    parser.add_argument("input_video", type=Path, help="path to an MP4 video")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = ingest_video(args.input_video)
    except VideoIngestionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    info = result.info
    print(f"Resolution: {info.width}x{info.height}")
    print(f"FPS: {info.fps:.3f}")
    print(f"Frame count: {info.frame_count}")
    print(f"Duration: {info.duration_seconds:.2f} seconds")
    print(f"Output: {result.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
