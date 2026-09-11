from __future__ import annotations

import argparse
from pathlib import Path

from epp_interpreter import EppError, EppInterpreter


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an E++ source file.")
    parser.add_argument("file", help="Path to an .epp file")
    args = parser.parse_args()

    source_path = Path(args.file)
    try:
        EppInterpreter().run(source_path.read_text(encoding="utf-8"))
    except EppError as exc:
        print(f"Error: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
