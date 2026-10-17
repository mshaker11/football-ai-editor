# Football AI Editor

A modular starting point for an AI-assisted soccer tactical video editor. Phase 1, Stage 1 handles video ingestion only: it reads an MP4 with OpenCV, reports its metadata, and writes a video copy to `outputs/`.

## Requirements

- Python 3.11 or newer
- OpenCV (installed from `requirements.txt`)

## Setup

From the project root, create and activate a virtual environment, then install the dependency:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS or Linux, use `python3 -m venv .venv` and `source .venv/bin/activate` for the first two commands.

## Usage

Put an MP4 in `videos/`, then pass its path to the program:

```sh
python main.py videos/match.mp4
```

The program prints the resolution, FPS, decoded frame count, and duration. It writes `outputs/match_copy.mp4`, retaining the input resolution and FPS. The output contains video frames only; OpenCV's video writer does not copy the audio track. The `outputs/` directory is created automatically.

If the input path does not exist, is not a file, is not an MP4, or cannot be decoded, the program prints a clear error and exits with a nonzero status.

## Tests

Run the ingestion unit tests with Python's standard library:

```sh
python -m unittest discover -s tests -v
```
