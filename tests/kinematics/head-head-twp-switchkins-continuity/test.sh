#!/bin/bash -e

if ! command -v pgrep >/dev/null; then
    echo "Refusing headless test: pgrep is unavailable" >&2
    exit 99
fi
if ! command -v ps >/dev/null; then
    echo "Refusing headless test: ps is unavailable" >&2
    exit 99
fi
if [ -e /tmp/linuxcnc.lock ]; then
    echo "Refusing headless test: /tmp/linuxcnc.lock already exists" >&2
    exit 99
fi

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

for process_name in linuxcnc linuxcncsvr milltask rtapi_app halsampler; do
    if process_is_live "$process_name"; then
        echo "Refusing headless test: $process_name is already running" >&2
        exit 99
    elif [ "$?" -ne 1 ]; then
        exit 99
    fi
done
if process_is_live probe_basic; then
    echo "Refusing headless test: Probe Basic is already running" >&2
    exit 99
elif [ "$?" -ne 1 ]; then
    exit 99
fi

rm -f sim.var sim.var.bak switchkins.samples
export PYTHONUNBUFFERED=1
if [ -e /tmp/linuxcnc.lock ]; then
    echo "Refusing headless test: /tmp/linuxcnc.lock appeared during preflight" >&2
    exit 99
fi
exec linuxcnc -r test.ini
