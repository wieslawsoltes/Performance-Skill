#!/usr/bin/env python3
"""Export an xctrace table using the syntax supported by installed Xcode."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run `xctrace export` after detecting whether the installed version "
            "requires `--input <trace>` or a positional trace path."
        )
    )
    parser.add_argument("trace", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--toc", action="store_true")
    mode.add_argument("--xpath")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.trace.exists():
        print(f"trace does not exist: {args.trace}", file=sys.stderr)
        return 2
    if args.output is not None and args.output.exists():
        print(f"output already exists: {args.output}", file=sys.stderr)
        return 2

    help_result = subprocess.run(
        ["xcrun", "xctrace", "help", "export"],
        check=False,
        capture_output=True,
        text=True,
    )
    help_text = f"{help_result.stdout}\n{help_result.stderr}"
    if help_result.returncode != 0:
        sys.stderr.write(help_text)
        return help_result.returncode

    command = ["xcrun", "xctrace", "export"]
    if "--input <file>" in help_text:
        command.extend(["--input", str(args.trace)])
    else:
        command.append(str(args.trace))

    if args.toc:
        command.append("--toc")
    else:
        command.extend(["--xpath", args.xpath])
    if args.output is not None:
        command.extend(["--output", str(args.output)])

    print(f"+ {shlex.join(command)}", file=sys.stderr)
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
