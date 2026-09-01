#!/bin/bash

set -u

ROOT=/home/cnc5/linuxcnc-dev
CONFIG=$ROOT/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic

export TWP_SPHERE_TEST_PROGRAM=$ROOT/nc_files/calibration/twp_sphere_full_cycle_bminus5_t4.ngc
export TWP_SPHERE_TEST_PASSES=$CONFIG/twp-sphere-full-cycle-bminus5-t4-passes.csv
export TWP_SPHERE_TEST_RESULTS=$CONFIG/twp-sphere-full-cycle-bminus5-t4-results.csv
export TWP_SPHERE_TEST_TARGET_B=-5.0
export TWP_SPHERE_TEST_TARGET_C=0.0
export TWP_SPHERE_TEST_CAMPAIGN=2026090102

exec "$(dirname "$0")/test.sh"
