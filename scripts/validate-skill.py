#!/usr/bin/env python3
"""Validate the structure and internal consistency of the Performance Skill."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
FENCED_BLOCK = re.compile(r"```(?P<language>[^\n]*)\n(?P<body>.*?)```", re.DOTALL)
COMMAND_LANGUAGES = {
    "",
    "bash",
    "console",
    "powershell",
    "pwsh",
    "sh",
    "shell",
    "text",
    "zsh",
}
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
    "references/index.md",
    "references/command-reference.md",
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
FOOTNOTED_DOCUMENTS = {
    "README.md",
    "SKILL.md",
    "references/index.md",
    "references/command-reference.md",
    "references/core/index.md",
    "references/runtime/index.md",
    "references/memory/index.md",
    "references/latency/index.md",
    "references/startup/index.md",
    "references/benchmarking/index.md",
    "references/production/index.md",
    "references/gpu/index.md",
    "references/platforms/index.md",
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def command_blocks(text: str) -> str:
    """Return executable-looking fenced blocks, excluding prose and source examples."""
    blocks: list[str] = []
    for match in FENCED_BLOCK.finditer(text):
        language = match.group("language").strip().lower().split(maxsplit=1)[0]
        if language in COMMAND_LANGUAGES:
            blocks.append(match.group("body"))
    return "\n".join(blocks)


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

    for relative in ("README.md", "LICENSE"):
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


def validate_footnotes(errors: list[str]) -> None:
    for relative in sorted(FOOTNOTED_DOCUMENTS):
        path = ROOT / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if "## Documentation footnotes" not in text:
            fail(errors, f"missing documentation footnotes section: {relative}")
        if not re.search(r"^\[\^[^\]]+\]:\s+", text, re.MULTILINE):
            fail(errors, f"missing Markdown footnote definitions: {relative}")


def validate_command_regressions(errors: list[str]) -> None:
    invalid_patterns = {
        r"dotnet-trace\s+collect(?!-linux)[\s\S]{0,300}?--profile\s+cpu-sampling":
            "removed standard dotnet-trace cpu-sampling profile",
        r"xcrun\s+xctrace\s+version\b":
            "undocumented xctrace version subcommand; use xcodebuild -version and xctrace help",
        r"xcrun\s+xctrace\s+export[\s\\\r\n]+--input\b":
            "invalid xctrace export --input form; trace path is positional",
        r"perf\s+sched\s+record[\s\\\r\n]+-p\b":
            "non-portable perf sched record -p form",
        r"CoreRuntime\.Core100\b":
            "invalid BenchmarkDotNet CoreRuntime.Core100 field",
        r"runqlat(?:-bpfcc)?\s+30\b":
            "assumed positional BCC runqlat duration; inspect the installed tool help",
    }

    for path in sorted(ROOT.rglob("*.md")):
        relative = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        commands = command_blocks(text)

        for pattern, message in invalid_patterns.items():
            if re.search(pattern, commands):
                fail(errors, f"{message} in {relative}")

        if "No license file currently exists" in text:
            fail(errors, f"stale license statement in {relative}")


def validate_text_hygiene(errors: list[str]) -> None:
    for path in sorted(ROOT.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        if "\t" in text:
            fail(errors, f"tab character in Markdown file: {path.relative_to(ROOT)}")


def main() -> int:
    errors: list[str] = []
    validate_front_matter(errors)
    validate_required_files(errors)
    validate_links(errors)
    validate_stale_paths(errors)
    validate_footnotes(errors)
    validate_command_regressions(errors)
    validate_text_hygiene(errors)

    if errors:
        print("Skill validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print("Skill validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
