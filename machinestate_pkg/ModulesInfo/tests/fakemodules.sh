#!/bin/bash

INP=${FAKEMODULES_INPUT}
if [ -z ${INP} ]; then
    exit 1
fi

cat ${INP}
