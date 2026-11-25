#!/usr/bin/env python3
"""L5: GitLab CE 15.11.13 -> 16.0.0. Feasibility measurement for this machine.

The images are amd64 only, so on Apple Silicon they run under emulation, and this lane
may use about 2.5 GiB of memory in total. This script answers one question before any
gate is attempted: does one GitLab instance become ready inside that memory limit within
a bounded time? It starts ONE from-version instance from nothing with a hard memory cap,
samples it until it is ready or the time bound is reached, records what it measured in
../../results/L5.json and removes the instance.

    SCREEN_SCRATCH=/some/dir [SCREEN_HOLD_FILE=/path/HOLD] python3 measure.py [--minutes 25]

If the instance is not ready inside the bound, the case is recorded as not-run with the
measurements as the reason. No gate observation is made by this script.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

CASE = "L5"
PORT = 28660
BASE = "http://127.0.0.1:%d" % PORT
REPO = "gitlab/gitlab-ce"
FROM_REF, TO_REF = "gitlab/gitlab-ce:15.11.13-ce.0", "gitlab/gitlab-ce:16.0.0-ce.0"
APP = "iu1b-l5-app"
MEMORY_CAP = "2500m"


def omnibus(root_password):
    """GitLab's documented settings for memory-constrained installations, plus the root password."""
    return "; ".join([
        "external_url 'http://127.0.0.1:%d'" % PORT,
        "nginx['listen_port'] = 80", "nginx['listen_https'] = false",
        "gitlab_rails['initial_root_password'] = '%s'" % root_password,
        "puma['worker_processes'] = 0", "sidekiq['max_concurrency'] = 5",
        "prometheus_monitoring['enable'] = false",
        "gitlab_rails['env'] = { 'MALLOC_CONF' => 'dirty_decay_ms:1000,muzzy_decay_ms:1000' }",
        "gitaly['env'] = { 'MALLOC_CONF' => 'dirty_decay_ms:1000,muzzy_decay_ms:1000' }",
        "gitlab_kas['enable'] = false", "registry['enable'] = false", "gitlab_pages['enable'] = false",
    ])


def mem_mib(text):
    value = text.split("/")[0].strip()
    for unit, factor in (("GiB", 1024.0), ("MiB", 1.0), ("KiB", 1 / 1024.0), ("B", 1 / 1048576.0)):
        if value.endswith(unit):
            return round(float(value[:-len(unit)]) * factor, 1)
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=float, default=25)
    parser.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                      "..", "..", "results", "L5.json"))
    args = parser.parse_args()
    sealed = lib.sealed_case(CASE)
    lib.scratch_dir(CASE)
    started = lib.utc_now()
    lib.wait_hold()
    lib.teardown(CASE)
    arch, digest = lib.sealed_digest(sealed, FROM_REF)
    pin = lib.pull_pinned(REPO, digest)
    today = lib.tag_resolves_today(FROM_REF, arch)
    images = [{"ref": FROM_REF, "sealed_platform": arch, "sealed_digest": digest, **pin,
               "pulled_digest_equals_sealed": any(d.endswith(digest) for d in pin["repo_digests"] or []),
               "tag_resolves_today_to": today, "tag_today_equals_sealed": (today == digest) if today else None},
              {"ref": TO_REF, "sealed_platform": "amd64",
               "sealed_digest": lib.sealed_digest(sealed, TO_REF)[1], "pulled": False,
               "reason": "not pulled: the from-version did not pass the feasibility measurement"}]
    info = lib.docker("info", "--format", "{{.NCPU}} CPUs, {{.MemTotal}} bytes, {{.Architecture}}, {{.ServerVersion}}").stdout.strip()
    others_before = [m for m in lib.memory_snapshot() if not m.startswith("iu1b-")]

    watch = lib.HoldWatch()
    lib.run_container(CASE, APP, pin["pulled_ref"], publish=[(PORT, 80)],
                      env={"GITLAB_OMNIBUS_CONFIG": omnibus(lib.new_secret(12))},
                      extra=["--platform", "linux/amd64", "--memory", MEMORY_CAP, "--memory-swap", MEMORY_CAP,
                             "--shm-size", "256m"])
    t0 = time.time()
    samples, ready_after, state = [], None, {}
    emulation = None
    while time.time() - t0 < args.minutes * 60:
        time.sleep(20)
        if lib.hold_active():
            break
        elapsed = int(time.time() - t0)
        fmt = "{{.State.Status}}|{{.State.OOMKilled}}|{{.State.ExitCode}}|{{.RestartCount}}|{{if .State.Health}}{{.State.Health.Status}}{{end}}"
        parts = lib.docker("inspect", APP, "--format", fmt, check=False).stdout.strip().split("|")
        state = dict(zip(("status", "oom_killed", "exit_code", "restart_count", "health"), parts))
        stats = lib.docker("stats", "--no-stream", "--format", "{{.MemUsage}}|{{.CPUPerc}}|{{.PIDs}}", APP,
                           check=False).stdout.strip().split("|")
        try:
            code, text, _ = lib.http("GET", BASE + "/users/sign_in", timeout=15)
        except Exception as exc:
            code, text = None, type(exc).__name__
        if emulation is None and state.get("status") == "running":
            emulation = lib.docker("exec", APP, "sh", "-c",
                                   "uname -m; tr '\\0' ' ' < /proc/self/cmdline", check=False).stdout.strip()[:200]
        samples.append({"elapsed_s": elapsed, "memory_mib": mem_mib(stats[0]) if stats and stats[0] else None,
                        "cpu": stats[1] if len(stats) > 1 else None, "pids": stats[2] if len(stats) > 2 else None,
                        "state": state, "http_users_sign_in": code})
        lib.log("L5 measure %4ds mem=%s cpu=%s http=%s state=%s" % (
            elapsed, samples[-1]["memory_mib"], samples[-1]["cpu"], code, state))
        if code == 200 and "sign_in" in text or code == 200:
            ready_after = elapsed
            break
        if state.get("status") != "running":
            break
    log_tail = lib.docker("logs", "--tail", "25", APP, check=False)
    log_tail = lib.redact_text((log_tail.stdout + log_tail.stderr))[-1800:]
    reconfigured = "gitlab Reconfigured!" in lib.docker("logs", APP, check=False).stdout
    hold = watch.record()
    lib.teardown(CASE)
    mems = [s["memory_mib"] for s in samples if s["memory_mib"] is not None]
    peak = max(mems) if mems else None
    cap_mib = 2500.0
    measured = {
        "what": "one from-version instance started from nothing under a hard memory cap, sampled every 20 s",
        "memory_cap": MEMORY_CAP + " (no swap beyond it)", "time_bound_minutes": args.minutes,
        "omnibus_settings": "GitLab's memory-constrained settings: puma single mode, sidekiq concurrency 5, "
                            "monitoring, registry, pages and the agent server off",
        "emulation_probe_uname_and_cmdline": emulation,
        "docker_vm": info, "other_sessions_containers_at_start": others_before,
        "ready_after_seconds": ready_after, "first_start_reconfigure_finished": reconfigured,
        "peak_memory_mib": peak, "peak_as_share_of_cap": round(peak / cap_mib, 3) if peak else None,
        "samples_at_or_above_95_percent_of_cap": sum(1 for m in mems if m >= 0.95 * cap_mib),
        "final_state": state, "samples": samples, "log_tail": log_tail, "hold": hold,
    }
    carried = ready_after is not None
    result = {
        "schema": "gammatron-real-upgrade-screen-result/v1",
        "case_id": CASE, "screen_lane": "iu1-b",
        "app": sealed["app"], "from_version": sealed["from_version"], "to_version": sealed["to_version"],
        "images": images,
        "conditions": {
            "host": "macOS on Apple Silicon, Docker Desktop; the images are linux/amd64 only and run under emulation",
            "memory_limit_of_this_lane": "about 2.5 GiB for all of its containers together",
        },
        "sealed": {
            "old_workflow_steps": sealed["old_workflow_steps"],
            "correct_path_on_to_version": sealed["correct_path_on_to_version"],
            "database_outcome": sealed["database_outcome"],
            "prediction_condition": sealed["prediction_condition"],
            "predicted_disposition": sealed["predicted_disposition"], "prediction_detail": sealed["prediction_detail"],
        },
        "feasibility_measurement": measured,
        "gates": {"A": "not run", "B": "not run", "C": "not run"},
        "disposition": "not-run" if not carried else "measurement-passed-gates-pending",
        "prediction": {"sealed": sealed["predicted_disposition"], "observed": None, "right": None,
                       "note": "not scored: no gate was run"},
        "deviations": [], "flags": [],
        "times_utc": {"started": started, "finished": lib.utc_now(), "clock": "date -u on the host"},
        "free_disk_gib_at_end": lib.free_disk_gib(),
    }
    lib.write_json(args.out, result)
    print(result["disposition"], "ready_after_s=%s peak_mib=%s state=%s" % (ready_after, peak, state))


if __name__ == "__main__":
    main()
