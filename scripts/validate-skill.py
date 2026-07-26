#!/usr/bin/env python3
"""Validate the structure and internal consistency of the Performance Skill."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
LEGACY_PATHS = {
    "references/core-workflow.md",
    "references/managed-runtime.md",
    "references/memory.md",
    "references/concurrency-io-latency.md",
    "references/startup-deployment.md",
    "references/benchmarking-validation.md",
    "references/production-containers.md",
    "references/gpu-rendering.md",
    "references/macos.md",
    "references/windows.md",
    "references/linux.md",
}
REQUIRED_DOMAIN_FILES = {
    "references/core/index.md",
    "references/core/guide.md",
    "references/runtime/index.md",
    "references/runtime/guide.md",
    "references/memory/index.md",
    "references/memory/guide.md",
    "references/latency/index.md",
    "references/latency/guide.md",
    "references/startup/index.md",
    "references/startup/guide.md",
    "references/benchmarking/index.md",
    "references/benchmarking/guide.md",
    "references/production/index.md",
    "references/production/guide.md",
    "references/gpu/index.md",
    "references/gpu/guide.md",
    "references/platforms/index.md",
    "references/platforms/macos.md",
    "references/platforms/windows.md",
    "references/platforms/linux.md",
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_front_matter(errors: list[str]) -> None:
    skill_files = sorted(ROOT.rglob("SKILL.md"))
    if skill_files != [ROOT / "SKILL.md"]:
        fail(errors, f"expected exactly one root SKILL.md, found: {skill_files}")
        return

    text = skill_files[0].read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(errors, "SKILL.md is missing opening YAML front matter")
        return

    try:
        _, front_matter, _ = text.split("---", 2)
    except ValueError:
        fail(errors, "SKILL.md has malformed YAML front matter delimiters")
        return

    for field in ("name:", "summary:", "description:"):
        if field not in front_matter:
            fail(errors, f"SKILL.md front matter is missing {field[:-1]}")


def validate_required_files(errors: list[str]) -> None:
    for relative in sorted(REQUIRED_DOMAIN_FILES):
        if not (ROOT / relative).is_file():
            fail(errors, f"missing required reference file: {relative}")

    for relative in ("README.md", "LICENSE", "references/index.md"):
        if not (ROOT / relative).is_file():
            fail(errors, f"missing required package file: {relative}")


def validate_links(errors: list[str]) -> None:
    for markdown in sorted(ROOT.rglob("*.md")):
        text = markdown.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK.finditer(text):
            target = match.group(1).strip()
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue

            path_part = target.split("#", 1)[0]
            if not path_part:
                continue

            resolved = (markdown.parent / path_part).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                fail(errors, f"link escapes repository: {markdown.relative_to(ROOT)} -> {target}")
                continue

            if not resolved.exists():
                fail(errors, f"broken relative link: {markdown.relative_to(ROOT)} -> {target}")


def validate_stale_paths(errors: list[str]) -> None:
    for path in sorted(ROOT.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for legacy in LEGACY_PATHS:
            if legacy in text:
                fail(errors, f"stale legacy path in {path.relative_to(ROOT)}: {legacy}")


def validate_command_regressions(errors: list[str]) -> None:
    for path in sorted(ROOT.rglob("*.md")):
        relative = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")

        # cpu-sampling is valid for collect-linux, but not for standard collect.
        if re.search(r"dotnet-trace\s+collect(?!-linux)[\s\S]{0,300}?--profile\s+cpu-sampling", text):
            fail(errors, f"removed standard dotnet-trace cpu-sampling profile in {relative}")

        if 'PackageReference Include="BenchmarkDotNet" Version="*"' in text:
            fail(errors, f"wildcard BenchmarkDotNet package version in {relative}")

        if "No license file currently exists" in text:
            fail(errors, f"stale license statement in {relative}")


def main() -> int:
    errors: list[str] = []
    validate_front_matter(errors)
    validate_required_files(errors)
    validate_links(errors)
    validate_stale_paths(errors)
    validate_command_regressions(errors)

    if errors:
        print("Skill validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print("Skill validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
