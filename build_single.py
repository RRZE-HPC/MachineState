#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, sys, os, pathlib, time

FILES = [
    "machinestate/common.py",
    "machinestate/BiosInfo.py",
    "machinestate/CacheTopology.py",
    "machinestate/CgroupInfo.py",
    "machinestate/ClocksourceInfo.py",
    "machinestate/CompilerInfo.py",
    "machinestate/CoretempInfo.py",
    "machinestate/CpuAffinity.py",
    "machinestate/CpuFrequency.py",
    "machinestate/CpuInfo.py",
    "machinestate/CpuTopology.py",
    "machinestate/DmiDecodeFile.py",
    "machinestate/ExecutableInfo.py",
    "machinestate/HostInfo.py",
    "machinestate/Hugepages.py",
    "machinestate/InfinibandInfo.py",
    "machinestate/IrqAffinity.py",
    "machinestate/KernelInfo.py",
    "machinestate/LoadAvg.py",
    "machinestate/MemInfo.py",
    "machinestate/ModulesInfo.py",
    "machinestate/MpiInfo.py",
    "machinestate/NecTsubasaInfo.py",
    "machinestate/NumaBalance.py",
    "machinestate/NumaInfo.py",
    "machinestate/NvidiaSmiInfo.py",
    "machinestate/OpenCLInfo.py",
    "machinestate/OperatingSystemInfo.py",
    "machinestate/PowercapInfo.py",
    "machinestate/PrefetcherInfo.py",
    "machinestate/PythonInfo.py",
    "machinestate/ShellEnvironment.py",
    "machinestate/ThermalZoneInfo.py",
    "machinestate/TransparentHugepages.py",
    "machinestate/TurboInfo.py",
    "machinestate/Uptime.py",
    "machinestate/UsersInfo.py",
    "machinestate/VulnerabilitiesInfo.py",
    "machinestate/WritebackInfo.py",
    "machinestate/WritebackWorkqueue.py",
    "machinestate/script.py",
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