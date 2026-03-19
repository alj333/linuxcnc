#!/bin/bash -e

rm -f sim.var
export PYTHONUNBUFFERED=1
exec linuxcnc -r test.ini
