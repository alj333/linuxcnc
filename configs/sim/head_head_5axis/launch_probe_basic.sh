#!/bin/bash
set -e

source /home/cnc5/dev/venv/bin/activate

if [ -f /home/cnc5/linuxcnc-dev/scripts/rip-environment ]; then
    source /home/cnc5/linuxcnc-dev/scripts/rip-environment
fi

cd /home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis
linuxcnc /home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/head_head_probe_basic.ini
