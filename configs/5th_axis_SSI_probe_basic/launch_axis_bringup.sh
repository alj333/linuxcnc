#!/bin/bash
set -e

if [ -f /home/cnc5/linuxcnc-dev/scripts/rip-environment ]; then
    source /home/cnc5/linuxcnc-dev/scripts/rip-environment
fi

cd /home/cnc5/linuxcnc-dev/configs/5th_axis_SSI_probe_basic
linuxcnc /home/cnc5/linuxcnc-dev/configs/5th_axis_SSI_probe_basic/5th_axis_axis_bringup.ini
