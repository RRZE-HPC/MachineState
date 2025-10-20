#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, sys, os, pathlib, time

FILES = [
    "machinestate_pkg/common.py",
    "machinestate_pkg/BiosInfo.py",
    "machinestate_pkg/CacheTopology.py",
    "machinestate_pkg/CgroupInfo.py",
    "machinestate_pkg/ClocksourceInfo.py",
    "machinestate_pkg/CompilerInfo.py",
    "machinestate_pkg/CoretempInfo.py",
    "machinestate_pkg/CpuAffinity.py",
    "machinestate_pkg/CpuFrequency.py",
    "machinestate_pkg/CpuInfo.py",
    "machinestate_pkg/CpuTopology.py",
    "machinestate_pkg/DmiDecodeFile.py",
    "machinestate_pkg/ExecutableInfo.py",
    "machinestate_pkg/HostInfo.py",
    "machinestate_pkg/Hugepages.py",
    "machinestate_pkg/InfinibandInfo.py",
    "machinestate_pkg/IrqAffinity.py",
    "machinestate_pkg/KernelInfo.py",
    "machinestate_pkg/LoadAvg.py",
    "machinestate_pkg/MemInfo.py",
    "machinestate_pkg/ModulesInfo.py",
    "machinestate_pkg/MpiInfo.py",
    "machinestate_pkg/NecTsubasaInfo.py",
    "machinestate_pkg/NumaBalance.py",
    "machinestate_pkg/NumaInfo.py",
    "machinestate_pkg/NvidiaSmiInfo.py",
    "machinestate_pkg/OpenCLInfo.py",
    "machinestate_pkg/OperatingSystemInfo.py",
    "machinestate_pkg/PowercapInfo.py",
    "machinestate_pkg/PrefetcherInfo.py",
    "machinestate_pkg/PythonInfo.py",
    "machinestate_pkg/ShellEnvironment.py",
    "machinestate_pkg/ThermalZoneInfo.py",
    "machinestate_pkg/TransparentHugepages.py",
    "machinestate_pkg/TurboInfo.py",
    "machinestate_pkg/Uptime.py",
    "machinestate_pkg/UsersInfo.py",
    "machinestate_pkg/VulnerabilitiesInfo.py",
    "machinestate_pkg/WritebackInfo.py",
    "machinestate_pkg/WritebackWorkqueue.py",
    "machinestate_pkg/script.py",
]

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

def main():
    root = pathlib.Path(__file__).parent
    out_path = root / OUT

    header = (
        "#!/usr/bin/env python3\n"
        f"# Auto-generated single-file MachineState ({time.strftime('%Y-%m-%d %H:%M:%S')})\n"
        "# Do not edit manually; edit sources and re-run build_single_py.py\n\n"
    )

    chunks = [header]

    for rel in FILES:
        src_path = root / rel
        if not src_path.exists():
            print(f"[warn] missing file: {rel}", file=sys.stderr)
            continue
        text = src_path.read_text(encoding='utf-8')

        text = strip_relative_imports(text)

        chunks.append(add_section_banner(rel))
        chunks.append(text.rstrip() + "\n")

    # Ensure only ONE top-level runner: rely on script.py:main()
    # If script.py doesn't have main(), you can add one here.
    result = "".join(chunks)

    out_path.write_text(result, encoding='utf-8')
    os.chmod(out_path, 0o755)
    print(f"[ok] wrote {OUT} ({out_path.stat().st_size} bytes)")

if __name__ == "__main__":
    main()