#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, sys, os, pathlib, time, glob
from typing import List

OUT = "machinestate.py"

# Regexes to strip package-relative imports and __main__ blocks
REL_IMPORT_RE = re.compile(r'^\s*from\s+\.\w+\s+import\s+.*$', re.M)
PKG_IMPORT_RE = re.compile(r'^\s*from\s+machinestate(?:\.\w+)?\s+import\s+.*$', re.M)

def strip_relative_imports(text: str) -> str:
    # Remove "from .X import Y"
    text = REL_IMPORT_RE.sub('', text)
    # Remove "from machinestate(.X)? import Y"
    text = PKG_IMPORT_RE.sub('', text)
    # Also remove "import machinestate" (rare)
    text = re.sub(r'^\s*import\s+machinestate\s*$', '', text, flags=re.M)
    return text

def add_section_banner(path: str) -> str:
    filename = os.path.basename(path)
    return (
        "\n\n" +
        "#" * 80 + "\n" +
        f"# BEGIN: {filename}\n" +
        "#" * 80 + "\n"
    )

def collect_files(root: pathlib.Path) -> List[str]:
    pkg = root / "machinestate_pkg"

    files = []

    common_py = pkg / "common.py"
    if common_py.exists():
        files.append(str(common_py))

    files.extend(sorted(glob.glob(str(pkg / "*" / "*.py"))))

    script_py = pkg / "script.py"
    if script_py.exists():
        files.append(str(script_py))

    return files

def main():
    root = pathlib.Path(__file__).parent
    out_path = root / OUT

    header = (
        "#!/usr/bin/env python3\n"
        f"# Auto-generated single-file MachineState ({time.strftime('%Y-%m-%d %H:%M:%S')})\n"
        "# Do not edit manually; edit sources and re-run build_single_py.py\n\n"
    )

    chunks = [header]

    for src in collect_files(root):
        src_path = pathlib.Path(src)
        rel = src_path.relative_to(root)

        if not src_path.exists():
            print(f"[warn] missing file: {rel}", file=sys.stderr)
            continue

        text = src_path.read_text(encoding="utf-8")
        text = strip_relative_imports(text)

        chunks.append(add_section_banner(str(rel)))
        chunks.append(text.rstrip() + "\n")

    result = "".join(chunks)

    out_path.write_text(result, encoding="utf-8")
    os.chmod(out_path, 0o755)
    print(f"[ok] wrote {OUT} ({out_path.stat().st_size} bytes)")

if __name__ == "__main__":
    main()