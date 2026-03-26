from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Print a text report with encoding fallbacks.")
    parser.add_argument(
        "path",
        nargs="?",
        default="reports/combined/final_analysis.txt",
        help="Report path to print. Defaults to reports/combined/final_analysis.txt",
    )
    args = parser.parse_args()

    file_path = Path(args.path).resolve()
    for encoding in ("utf-8", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            print(file_path.read_text(encoding=encoding))
            return
        except Exception:
            continue
    raise SystemExit(f"Unable to decode {file_path}")


if __name__ == "__main__":
    main()
