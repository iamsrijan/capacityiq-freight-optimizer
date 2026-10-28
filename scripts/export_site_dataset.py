from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
OUTPUT_PATH = ROOT_DIR / "app" / "data" / "site-dataset.json"

sys.path.insert(0, str(BACKEND_DIR))

from repository import dataset_summary, load_dataset  # noqa: E402


def main() -> None:
    dataset = load_dataset()
    payload = {
        "corridors": dataset["corridors"],
        "retailProfiles": dataset["retailProfiles"],
        "airCarriers": dataset["airCarriers"],
        "summary": dataset_summary(dataset),
    }
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=True, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Exported hosted dataset to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
