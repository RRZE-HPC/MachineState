#!/bin/bash
set -e

BASE_OUT="tests/full/sys/devices/virtual/dmi/id"
mkdir -p "$BASE_OUT"

for f in bios_date bios_vendor bios_version sys_vendor product_name product_vendor; do
    if [ -f "/sys/devices/virtual/dmi/id/$f" ]; then
        cp "/sys/devices/virtual/dmi/id/$f" "$BASE_OUT/"
    fi
done

mkdir -p tests/no_product_vendor/sys/devices/virtual/dmi/id
cp tests/full/sys/devices/virtual/dmi/id/bios_date      tests/no_product_vendor/sys/devices/virtual/dmi/id/
cp tests/full/sys/devices/virtual/dmi/id/bios_vendor    tests/no_product_vendor/sys/devices/virtual/dmi/id/
cp tests/full/sys/devices/virtual/dmi/id/bios_version   tests/no_product_vendor/sys/devices/virtual/dmi/id/
cp tests/full/sys/devices/virtual/dmi/id/sys_vendor     tests/no_product_vendor/sys/devices/virtual/dmi/id/
cp tests/full/sys/devices/virtual/dmi/id/product_name   tests/no_product_vendor/sys/devices/virtual/dmi/id/

mkdir -p tests/missing_base