#!/usr/bin/env python3
"""Validate a generated skill folder and zip it into <name>.skill for claude.ai upload.

Usage: package.py SKILL_DIR [OUT_DIR]
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path


def validate(skill: Path) -> list[str]:
    problems = []
    md = skill / "SKILL.md"
    if not md.exists():
        return ["SKILL.md missing"]
    text = md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return ["SKILL.md has no YAML frontmatter"]
    fm = m.group(1)
    name = re.search(r"^name:\s*(.+)$", fm, re.M)
    desc = re.search(r"^description:\s*(.+)$", fm, re.M)
    if not name:
        problems.append("frontmatter: name missing")
    elif not re.fullmatch(r"[a-z0-9-]{1,64}", name.group(1).strip()):
        problems.append("frontmatter: name must be lowercase letters, digits, hyphens (max 64)")
    if not desc:
        problems.append("frontmatter: description missing")
    elif len(desc.group(1)) > 1024:
        problems.append("frontmatter: description over 1024 characters")
    lines = text.count("\n")
    if lines > 500:
        problems.append(f"SKILL.md is {lines} lines; move detail into references/ (aim < 500)")
    for ref in re.findall(r"\]\(((?:references|assets)/[^)#]+)\)", text):
        if not (skill / ref).exists():
            problems.append(f"broken link: {ref}")
    return problems


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    skill = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else skill.parent
    problems = validate(skill)
    for p in problems:
        print(f"[package] {p}")
    if problems:
        return 1
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"{skill.name}.skill"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(skill.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                z.write(f, Path(skill.name) / f.relative_to(skill))
    print(f"[package] OK -> {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
