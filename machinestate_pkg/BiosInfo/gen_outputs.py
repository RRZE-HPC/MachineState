#!/usr/bin/env python3

import os
import os.path
import sys
sys.path.append("..")

from unittest.mock import patch

import BiosInfo

BASEDIR = "./tests"
REAL_BASE = "/sys/devices/virtual/dmi/id"


def redirect_path(path, fake_base):
    if path == REAL_BASE:
        return fake_base
    if path.startswith(REAL_BASE + "/"):
        suffix = path[len(REAL_BASE) + 1:]
        return os.path.join(fake_base, suffix)
    return path


def generate_output(case_name):
    testfolder = os.path.join(BASEDIR, case_name)
    fake_base = os.path.join(testfolder, "sys/devices/virtual/dmi/id")

    def fake_pexists(path):
        return os.path.exists(redirect_path(path, fake_base))

    def fake_pjoin(a, *parts):
        joined = os.path.join(a, *parts)
        return redirect_path(joined, fake_base)

    with patch("BiosInfo.pexists", side_effect=fake_pexists), \
         patch("BiosInfo.pjoin", side_effect=fake_pjoin):

        c = BiosInfo.BiosInfo()

        if hasattr(c, "generate"):
            c.generate()
        c.update()

        output = c.get_json()

    with open(os.path.join(testfolder, "output"), "w", encoding="utf-8") as f:
        f.write(output)
        if not output.endswith("\n"):
            f.write("\n")

    print(f"Wrote {testfolder}/output")


def main():
    for case_name in ["full", "no_product_vendor", "missing_base"]:
        generate_output(case_name)


if __name__ == "__main__":
    main()