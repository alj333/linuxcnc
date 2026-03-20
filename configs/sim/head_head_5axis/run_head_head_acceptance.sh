#!/bin/bash
set -u

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
REPO_DIR=$(cd "$SCRIPT_DIR/../../.." && pwd)
LOG_ROOT=${HEAD_HEAD_ACCEPTANCE_LOG_DIR:-"/tmp/head_head_acceptance_$(date +%Y%m%d_%H%M%S)"}
STOP_ON_FAIL=0
COOLDOWN_SECONDS=${HEAD_HEAD_ACCEPTANCE_COOLDOWN_SECONDS:-3}
MAX_RT_RETRIES=${HEAD_HEAD_ACCEPTANCE_RT_RETRIES:-2}

usage() {
    cat <<EOF
Usage: $(basename "$0") [--stop-on-fail] [--logs DIR]

Runs the automated head-head software acceptance checks and verifies the
expected output patterns from each test harness.

Options:
  --stop-on-fail   Stop after the first failing test
  --logs DIR       Write logs to DIR instead of $LOG_ROOT
  --help           Show this help
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --stop-on-fail)
            STOP_ON_FAIL=1
            shift
            ;;
        --logs)
            LOG_ROOT="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

mkdir -p "$LOG_ROOT"

run_test_once() {
    local workdir=$1
    (
        cd "$workdir" || exit 1
        set +u
        source "$REPO_DIR/scripts/rip-environment"
        set -u
        if [ -f ./test.sh ]; then
            ./test.sh
        else
            linuxcnc -r test.ini
        fi
    )
}

is_realtime_startup_race() {
    local logfile=$1
    grep -Eq \
        'lockfile still not removed|rtapi_app exited without becoming ready|insmod for (homemod|headheadkins) failed' \
        "$logfile"
}

TESTS=(
  "twp_g0g1|tests/kinematics/head-head-twp-g0g1|pause 14 ok;;program complete"
  "twp_requires_tcpc|tests/kinematics/head-head-twp-requires-tcpc|TWP mode enable requested while TCPC mode is not enabled"
  "twp_reject_rotary|tests/kinematics/head-head-twp-reject-rotary|Linear move on line 11 fails kinematicsInverse"
  "twp_reject_tool_length|tests/kinematics/head-head-twp-reject-tool-length|Cannot change tool length compensation while TWP is active"
  "twp_reject_tool_change|tests/kinematics/head-head-twp-reject-tool-change|Cannot change tools while TWP is active"
  "twp_reject_tool_number|tests/kinematics/head-head-twp-reject-tool-number|Cannot change current tool number while TWP is active"
  "twp_tooling_after_g69|tests/kinematics/head-head-twp-tooling-after-g69|pause 7 ok;;program complete"
  "twp_limit_reject|tests/kinematics/head-head-twp-limit-reject|positive limit"
  "twp_limit_recovery|tests/kinematics/head-head-twp-limit-recovery|recovery step 6 ok"
  "twp_abort_state|tests/kinematics/head-head-twp-abort-state|abort state ok;;abort recovery ok"
  "twp_estop_reset|tests/kinematics/head-head-twp-estop-reset|post-estop recovery cancel ok"
  "twp_rehome_reset|tests/kinematics/head-head-twp-rehome-reset|rehome clear ok;;post-rehome recovery cancel ok"
  "twp_manual_bc_entry|tests/kinematics/head-head-twp-manual-bc-entry|pause 11 ok;;program complete"
  "twp_queuebuster|tests/remap/head-head-twp-queuebuster|pause 8 ok;;program complete"
)

PASS_COUNT=0
FAIL_COUNT=0

echo "Head-head acceptance logs: $LOG_ROOT"
echo

for entry in "${TESTS[@]}"; do
    IFS="|" read -r name rel_dir pattern_blob <<<"$entry"
    workdir="$REPO_DIR/$rel_dir"
    logfile="$LOG_ROOT/${name}.log"

    echo "==> $name"
    attempt=1
    while :; do
        if [ $attempt -gt 1 ]; then
            echo "retrying $name after realtime cleanup race (attempt $attempt/$((MAX_RT_RETRIES + 1)))"
            sleep "$COOLDOWN_SECONDS"
        fi

        run_test_once "$workdir" >"$logfile" 2>&1
        rc=$?

        if [ $rc -eq 0 ]; then
            break
        fi

        if [ $attempt -gt $MAX_RT_RETRIES ] || ! is_realtime_startup_race "$logfile"; then
            break
        fi

        attempt=$((attempt + 1))
    done

    status="PASS"
    missing=""

    if [ $rc -ne 0 ]; then
        status="FAIL"
        missing="non-zero exit ($rc)"
    else
        IFS=";;" read -r -a patterns <<<"$pattern_blob"
        for pattern in "${patterns[@]}"; do
            if ! grep -Fq "$pattern" "$logfile"; then
                status="FAIL"
                if [ -n "$missing" ]; then
                    missing="$missing, "
                fi
                missing="${missing}missing pattern: $pattern"
            fi
        done
    fi

    if [ "$status" = "PASS" ]; then
        PASS_COUNT=$((PASS_COUNT + 1))
        echo "PASS  $name"
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
        echo "FAIL  $name"
        echo "      $missing"
        echo "      log: $logfile"
        echo "      tail:"
        tail -n 20 "$logfile" | sed 's/^/        /'
        if [ $STOP_ON_FAIL -eq 1 ]; then
            break
        fi
    fi
    echo

    sleep "$COOLDOWN_SECONDS"
done

echo "Summary: $PASS_COUNT passed, $FAIL_COUNT failed"
echo "Logs: $LOG_ROOT"

if [ $FAIL_COUNT -ne 0 ]; then
    exit 1
fi
