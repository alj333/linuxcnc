#!/bin/bash
set -euo pipefail

base=/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic
stamp=$(date '+%Y%m%d_%H%M%S')
output="$base/diagnostics/task_exit_captures/probe-edges-a3-$stamp.csv"

exec python3 "$base/diagnostics/monitor_tcpc_probe_edges.py" \
  --component-name tcpc_probe_edge_monitor \
  --sample-hz 100 \
  --heartbeat 1 \
  --pin-wait-timeout 60 \
  --output "$output"
