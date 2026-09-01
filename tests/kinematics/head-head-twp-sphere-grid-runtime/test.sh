#!/bin/bash

set -u

PASS_CSV=/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/twp-sphere-grid-low-angle-t4-passes.csv
POSE_CSV=/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/twp-sphere-grid-low-angle-t4-poses.csv
SUMMARY_CSV=/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/twp-sphere-grid-low-angle-t4-summary.csv
BACKUP_DIR=

process_is_live() {
    local name=$1
    local pid state
    local found=1

    while read -r pid; do
        [ -n "$pid" ] || continue
        state=$(ps -o stat= -p "$pid" 2>/dev/null) || continue
        case "$state" in
            Z*|X*) ;;
            *) found=0 ;;
        esac
    done < <(pgrep -x "$name" 2>/dev/null || true)
    return "$found"
}

preflight() {
    local name

    for command in pgrep ps cmp cp mktemp; do
        command -v "$command" >/dev/null 2>&1 || {
            echo "Refusing headless test: $command is unavailable" >&2
            return 99
        }
    done
    [ ! -e /tmp/linuxcnc.lock ] || {
        echo "Refusing headless test: /tmp/linuxcnc.lock already exists" >&2
        return 99
    }
    for name in linuxcnc linuxcncsvr milltask rtapi_app halsampler probe_basic; do
        if process_is_live "$name"; then
            echo "Refusing headless test: $name is already running" >&2
            return 99
        fi
    done
    [ -f "$PASS_CSV" ] || {
        echo "Missing production pass CSV: $PASS_CSV" >&2
        return 99
    }
    [ -f "$POSE_CSV" ] || {
        echo "Missing production pose CSV: $POSE_CSV" >&2
        return 99
    }
    [ -f "$SUMMARY_CSV" ] || {
        echo "Missing production summary CSV: $SUMMARY_CSV" >&2
        return 99
    }
}

restore_artifacts() {
    local status=$1
    local cleanup_failed=0
    local restore_failed=0
    local name

    set +e
    trap - EXIT HUP INT TERM
    for attempt in $(seq 1 100); do
        [ ! -e /tmp/linuxcnc.lock ] || { sleep 0.05; continue; }
        local any_live=0
        for name in linuxcnc linuxcncsvr milltask rtapi_app halsampler; do
            process_is_live "$name" && any_live=1
        done
        [ "$any_live" -eq 0 ] && break
        sleep 0.05
    done
    [ ! -e /tmp/linuxcnc.lock ] || {
        echo "Headless test left /tmp/linuxcnc.lock" >&2
        cleanup_failed=1
    }
    for name in linuxcnc linuxcncsvr milltask rtapi_app halsampler; do
        if process_is_live "$name"; then
            echo "Headless test left $name running" >&2
            cleanup_failed=1
        fi
    done

    if [ -n "$BACKUP_DIR" ] && [ -d "$BACKUP_DIR" ]; then
        if [ "$cleanup_failed" -eq 0 ]; then
            cp -- "$BACKUP_DIR/passes.csv" "$PASS_CSV" || restore_failed=1
            cp -- "$BACKUP_DIR/poses.csv" "$POSE_CSV" || restore_failed=1
            cp -- "$BACKUP_DIR/summary.csv" "$SUMMARY_CSV" || restore_failed=1
            cmp -s -- "$BACKUP_DIR/passes.csv" "$PASS_CSV" || restore_failed=1
            cmp -s -- "$BACKUP_DIR/poses.csv" "$POSE_CSV" || restore_failed=1
            cmp -s -- "$BACKUP_DIR/summary.csv" "$SUMMARY_CSV" || restore_failed=1
        else
            restore_failed=1
        fi
        if [ "$restore_failed" -eq 0 ]; then
            echo "Production sphere CSV restoration verified byte-for-byte"
            rm -rf -- "$BACKUP_DIR" || restore_failed=1
        fi
    else
        echo "Production sphere CSV backup directory is unavailable" >&2
        restore_failed=1
    fi

    if [ "$cleanup_failed" -ne 0 ] || [ "$restore_failed" -ne 0 ]; then
        echo "Production CSV restoration or cleanup verification failed" >&2
        [ -z "$BACKUP_DIR" ] || echo "Original CSV backup retained at $BACKUP_DIR" >&2
        exit 98
    fi
    exit "$status"
}

preflight || exit $?
BACKUP_DIR=$(mktemp -d /tmp/twp-sphere-grid-runtime.XXXXXX) || exit 99
cp -- "$PASS_CSV" "$BACKUP_DIR/passes.csv" || exit 99
cp -- "$POSE_CSV" "$BACKUP_DIR/poses.csv" || exit 99
cp -- "$SUMMARY_CSV" "$BACKUP_DIR/summary.csv" || exit 99
trap 'restore_artifacts $?' EXIT HUP INT TERM

rm -f sim.var sim.var.bak
export PYTHONUNBUFFERED=1
linuxcnc -r test.ini
status=$?

# The EXIT trap restores all hard-coded production log targets and verifies
# byte identity after LinuxCNC has closed every logger.
exit "$status"
