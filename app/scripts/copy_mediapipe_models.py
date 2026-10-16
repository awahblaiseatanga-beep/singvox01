from __future__ import annotations

import argparse
import shutil
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MODEL_NAMES = (
    "pose_landmarker.task",
    "hand_landmarker.task",
    "face_landmarker.task",
)


def copy_models(source: Path, destination: Path) -> None:
    missing = [name for name in MODEL_NAMES if not (source / name).is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing local MediaPipe model file(s): "
            + ", ".join(missing)
            + ". Run the repository MediaPipe model downloader first."
        )

    destination.mkdir(parents=True, exist_ok=True)
    for name in MODEL_NAMES:
        source_file = source / name
        if source_file.stat().st_size == 0:
            raise ValueError(f"MediaPipe model file is empty: {source_file}")
        shutil.copy2(source_file, destination / name)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy local MediaPipe Tasks bundles into Android's ignored app assets."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=REPOSITORY_ROOT / "mediapipe_models",
        help="Directory containing the three local .task bundles.",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=REPOSITORY_ROOT
        / "app"
        / "android"
        / "app"
        / "src"
        / "main"
        / "assets"
        / "mediapipe_models",
        help="Android asset directory; .task files remain ignored by Git.",
    )
    args = parser.parse_args()
    copy_models(args.source, args.destination)
    print(f"Copied {len(MODEL_NAMES)} MediaPipe task bundles into {args.destination}")


if __name__ == "__main__":
    main()
