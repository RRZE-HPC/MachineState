#!/usr/bin/env python3
import sys, os, os.path, glob as stdglob
from unittest.mock import patch

sys.path.append("..")
import ClocksourceInfo

BASE = "./tests"
REAL_CLOCKSOURCE_PATH = "/sys/devices/system/clocksource"
REAL_CLOCKSOURCE_SEARCH = REAL_CLOCKSOURCE_PATH + "/clocksource*"

def redirect_path(path, fake_base):
    if path == REAL_CLOCKSOURCE_PATH:
        return fake_base
    if path == REAL_CLOCKSOURCE_SEARCH:
        return os.path.join(fake_base, "clocksource*")
    if path.startswith(REAL_CLOCKSOURCE_PATH + "/"):
        suffix = path[len(REAL_CLOCKSOURCE_PATH) + 1:]
        return os.path.join(fake_base, suffix)
    return path

def build_output(testfolder, extended=False):
    fake_base = os.path.join(testfolder, "sys/devices/system/clocksource")

    def fake_pjoin(a, *parts):
        return redirect_path(os.path.join(a, *parts), fake_base)

    def fake_glob(pattern):
        return stdglob.glob(redirect_path(pattern, fake_base))

    with patch("ClocksourceInfo.pjoin", side_effect=fake_pjoin), \
         patch("common.glob", side_effect=fake_glob):
        c = ClocksourceInfo.ClocksourceInfo(extended=extended)
        c.generate()
        c.update()
        j = c.get_json()

    with open(os.path.join(testfolder, "output"), "w", encoding="utf-8") as f:
        f.write(j + "\n")

build_output(os.path.join(BASE, "full"), extended=False)
build_output(os.path.join(BASE, "extended"), extended=True)
build_output(os.path.join(BASE, "missing_current"), extended=False)

print("Wrote output files.")