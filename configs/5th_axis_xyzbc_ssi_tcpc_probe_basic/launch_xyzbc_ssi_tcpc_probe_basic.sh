#!/bin/bash
set -e

source /home/cnc5/dev/venv/bin/activate

if [ -f /home/cnc5/linuxcnc-dev/scripts/rip-environment ]; then
    source /home/cnc5/linuxcnc-dev/scripts/rip-environment
fi

cd /home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic
linuxcnc /home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/5th_axis_xyzbc_ssi_tcpc_probe_basic_length_model_validation_2026082601.ini
