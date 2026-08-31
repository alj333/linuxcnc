#!/bin/bash

set -euo pipefail

TEST_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$TEST_DIR"

STAGE_PID=""
PROCESS_NAMES=(linuxcnc linuxcncsvr milltask rtapi_app halsampler)

process_is_live() {
    local process_name="$1"
    local pgrep_status=0
    local pid
    local pids
    local ps_status
    local state

    pids=$(pgrep -x "$process_name") || pgrep_status=$?
    case "$pgrep_status" in
        0) ;;
        1) return 1 ;;
        *)
            echo "Refusing headless test: cannot inspect $process_name processes" >&2
            return 2
            ;;
    esac

    while read -r pid; do
        [ -n "$pid" ] || continue
        ps_status=0
        state=$(ps -o stat= -p "$pid" 2>/dev/null) || ps_status=$?
        if [ "$ps_status" -ne 0 ] || [ -z "$state" ]; then
            if [ -e "/proc/$pid/stat" ]; then
                echo "Refusing headless test: cannot inspect PID $pid ($process_name)" >&2
                return 2
            fi
            continue
        fi
        case "$state" in
            Z*|X*) ;;
            *) return 0 ;;
        esac
    done <<< "$pids"
    return 1
}

wait_for_shutdown() {
    local deadline=$((SECONDS + 30))
    local process_name

    while [ "$SECONDS" -lt "$deadline" ]; do
        local live=0
        for process_name in "${PROCESS_NAMES[@]}"; do
            if process_is_live "$process_name"; then
                live=1
                break
            elif [ "$?" -ne 1 ]; then
                return 1
            fi
        done
        if [ "$live" -eq 0 ] \
            && [ ! -e /tmp/linuxcnc.lock ] \
            && ! pgrep -f '[h]eadhead_twp_state_tcpc_off.py' >/dev/null; then
            return 0
        fi
        sleep 0.1
    done
    echo "Timed out waiting for complete LinuxCNC shutdown" >&2
    return 1
}

cleanup() {
    local status=$?
    trap - EXIT INT TERM
    if [ -n "$STAGE_PID" ]; then
        kill -TERM -- "-$STAGE_PID" 2>/dev/null || true
        sleep 1
        kill -KILL -- "-$STAGE_PID" 2>/dev/null || true
        wait "$STAGE_PID" 2>/dev/null || true
    fi
    STAGE_PID=""
    wait_for_shutdown || status=1
    rm -f sim.var sim.var.bak .component-loss-stage1.ok
    exit "$status"
}

run_stage() {
    local stage="$1"
    local launch_status=0

    echo "Launching isolated TWP recovery stage: $stage"
    TWP_RECOVERY_STAGE="$stage" setsid linuxcnc -r test.ini &
    STAGE_PID=$!
    wait "$STAGE_PID" || launch_status=$?
    if [ "$launch_status" -ne 0 ]; then
        echo "LinuxCNC $stage stage failed with status $launch_status" >&2
        return "$launch_status"
    fi
    wait_for_shutdown
    STAGE_PID=""
}

if ! command -v pgrep >/dev/null || ! command -v ps >/dev/null; then
    echo "Refusing headless test: pgrep and ps are required" >&2
    exit 99
fi
if ! command -v setsid >/dev/null; then
    echo "Refusing headless test: setsid is required" >&2
    exit 99
fi
if [ -e /tmp/linuxcnc.lock ]; then
    echo "Refusing headless test: /tmp/linuxcnc.lock already exists" >&2
    exit 99
fi
for process_name in "${PROCESS_NAMES[@]}"; do
    if process_is_live "$process_name"; then
        echo "Refusing headless test: $process_name is already running" >&2
        exit 99
    elif [ "$?" -ne 1 ]; then
        exit 99
    fi
done
if pgrep -f '[h]eadhead_twp_state_tcpc_off.py' >/dev/null; then
    echo "Refusing headless test: a headheadtwp state component is already running" >&2
    exit 99
fi

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
rm -f sim.var sim.var.bak .component-loss-stage1.ok

run_stage loss
if [ ! -s .component-loss-stage1.ok ]; then
    echo "Loss stage did not publish its success marker" >&2
    exit 1
fi

# Do not let interpreter parameters or tool state participate in recovery. The
# second invocation must reconstruct all controller and HAL state from startup.
rm -f sim.var sim.var.bak
run_stage recovery

rm -f sim.var sim.var.bak .component-loss-stage1.ok
wait_for_shutdown
trap - EXIT INT TERM
echo "TWP userspace-component loss and restart-only recovery test complete"
