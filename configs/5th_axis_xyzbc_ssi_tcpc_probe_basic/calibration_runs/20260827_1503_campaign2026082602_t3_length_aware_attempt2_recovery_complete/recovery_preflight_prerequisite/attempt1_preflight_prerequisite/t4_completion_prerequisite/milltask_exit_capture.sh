#!/usr/bin/env bash

# Parent wrapper for diagnosing silent milltask exits. The child receives the
# original arguments and inherited environment unchanged.

set -u

real_task=${MILLTASK_REAL_TASK:-/home/cnc5/linuxcnc-dev/bin/milltask}
capture_root=${MILLTASK_CAPTURE_ROOT:-/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/diagnostics/task_exit_captures}
stamp=$(date +%Y%m%d_%H%M%S)
mkdir -p "$capture_root"
log="$capture_root/milltask-$stamp.log"

{
    printf 'wrapper_started='; date --iso-8601=ns
    printf 'wrapper_pid=%s\n' "$$"
    printf 'cwd=%s\n' "$PWD"
    printf 'real_task=%s\n' "$real_task"
    sha256sum "$real_task"
    readelf -n "$real_task" 2>/dev/null | grep -F 'Build ID:' || true
    printf 'argv='
    printf '%q ' "$@"
    printf '\n'
    printf 'core_pattern='
    cat /proc/sys/kernel/core_pattern 2>&1
    printf 'core_limit_before=%s\n' "$(ulimit -c)"
} >> "$log"

if [[ -e "$PWD/core" ]]; then
    mv -- "$PWD/core" "$capture_root/preexisting-core-$stamp"
    printf 'preserved_preexisting_core=%s\n' "$capture_root/preexisting-core-$stamp" >> "$log"
fi

ulimit -c unlimited
printf 'core_limit_child=%s\n' "$(ulimit -c)" >> "$log"

"$real_task" "$@" &
child=$!
printf 'milltask_pid=%s\n' "$child" >> "$log"
{
    printf '\nchild_status_at_launch:\n'
    sed -n '1,45p' "/proc/$child/status" 2>&1
    printf '\nchild_limits_at_launch:\n'
    cat "/proc/$child/limits" 2>&1
} >> "$log"

wait "$child"
status=$?

{
    printf 'child_finished='; date --iso-8601=ns
    printf 'wait_status=%s\n' "$status"
    if (( status >= 128 )); then
        printf 'shell_signal_number=%s\n' "$((status - 128))"
    else
        printf 'normal_exit_code=%s\n' "$status"
    fi
} >> "$log"

backtrace=/tmp/backtrace.$child
if [[ -f "$backtrace" ]]; then
    backtrace_target="$capture_root/backtrace-$stamp-milltask-$child.txt"
    cp -- "$backtrace" "$backtrace_target"
    printf 'backtrace_file=%s\n' "$backtrace_target" >> "$log"
else
    printf 'backtrace_file=none\n' >> "$log"
fi

if [[ -f "$PWD/core" ]]; then
    core_target="$capture_root/core-$stamp-milltask-$child"
    mv -- "$PWD/core" "$core_target"
    printf 'core_file=%s\n' "$core_target" >> "$log"
else
    printf 'core_file=none\n' >> "$log"
fi

case "$status" in
    0)
        if [[ -f "$backtrace" ]]; then
            printf 'classification=caught_signal_handler_or_normal_shutdown_after_backtrace\n' >> "$log"
        else
            printf 'classification=normal_exit\n' >> "$log"
        fi
        ;;
    1) printf 'classification=designed_error_exit_or_startup_failure\n' >> "$log" ;;
    134) printf 'classification=probable_sigabrt\n' >> "$log" ;;
    137) printf 'classification=probable_sigkill\n' >> "$log" ;;
    139) printf 'classification=probable_uncaught_sigsegv\n' >> "$log" ;;
    *)
        if (( status >= 128 )); then
            printf 'classification=probable_signal_%s\n' "$((status - 128))" >> "$log"
        else
            printf 'classification=other_exit_%s\n' "$status" >> "$log"
        fi
        ;;
esac

exit "$status"
