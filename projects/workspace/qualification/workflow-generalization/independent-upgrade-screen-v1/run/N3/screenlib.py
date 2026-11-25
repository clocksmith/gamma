"""Helpers shared by the runners of the independent real-upgrade screen (Python standard library only).

Nothing secret is written by these helpers: request headers are recorded with the credential redacted, and
state files are read from outside the repository.

Environment:
  SCREEN_HOLD_FILE   path of the hold marker; while it exists nothing is started and observations are void
  SCREEN_OUT_DIR     directory for the raw per-repeat evidence (outside the repository while a run is going)
  GAMMATRON_QUAL_STATE  directory of the bring-up state files (default: the bring-up scripts' default)
"""
import json
import os
import subprocess
import threading
import time
import urllib.error
import urllib.request

HOLD_FILE = os.environ.get("SCREEN_HOLD_FILE", "")
BODY_EXCERPT_CHARS = 2500


def utc_now():
    """UTC time from `date -u`."""
    return subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True).stdout.strip()


def hold_exists():
    return bool(HOLD_FILE) and os.path.exists(HOLD_FILE)


def wait_for_no_hold():
    """Block while the hold marker exists, checking every 30 seconds. Returns the seconds waited."""
    waited = 0
    while hold_exists():
        time.sleep(30)
        waited += 30
    return waited


class SuspendWatch(threading.Thread):
    """Notices when this process was stopped (a hold stops it): a gap of more than 5 s between 1 s ticks."""

    def __init__(self):
        super().__init__(daemon=True)
        self.gaps = []
        self._last = time.time()

    def run(self):
        while True:
            time.sleep(1)
            now = time.time()
            if now - self._last > 5:
                self.gaps.append({"gap_seconds": round(now - self._last, 1), "noticed_at_utc": utc_now()})
            self._last = now


class Recorder:
    """Collects raw observations: every request, every response, every database read."""

    def __init__(self):
        self.watch = SuspendWatch()
        self.watch.start()

    def http(self, events, label, method, base_url, path, auth, credential_note, body=None, timeout=120,
             recorded_body=None):
        """Send one request and append the raw exchange to `events`.

        `auth` maps credential header names to values (Authorization or Cookie); they are recorded redacted.
        `recorded_body` replaces the body in the record when the body itself holds a secret (a log-in).
        Returns {"status", "json", "text", "headers"}."""
        hold_before = hold_exists()
        data = json.dumps(body).encode() if body is not None else None
        headers = {**auth, "Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(base_url + path, data=data, method=method, headers=headers)
        started = utc_now()
        t0 = time.time()
        status, text, error, response_headers = None, "", None, {}
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status, text = response.status, response.read().decode("utf-8", "replace")
                response_headers = response.headers
        except urllib.error.HTTPError as e:
            status, text, response_headers = e.code, e.read().decode("utf-8", "replace"), e.headers
        except Exception as e:  # connection refused, timeout
            error = f"{type(e).__name__}: {e}"
        elapsed = round(time.time() - t0, 3)
        events.append({
            "kind": "http", "label": label, "method": method, "base_url": base_url, "path": path,
            "request_headers": {**{name: f"<redacted> ({credential_note})" for name in auth},
                                **({"Content-Type": "application/json"} if data is not None else {})},
            "request_body": body if recorded_body is None else recorded_body, "response_status": status,
            "response_body_excerpt": text[:BODY_EXCERPT_CHARS],
            "response_body_chars": len(text), "transport_error": error,
            "started_utc": started, "elapsed_seconds": elapsed,
            "hold_marker_before": hold_before, "hold_marker_after": hold_exists(),
        })
        parsed = None
        try:
            parsed = json.loads(text) if text else None
        except ValueError:
            pass
        return {"status": status, "json": parsed, "text": text, "headers": response_headers}

    def command(self, events, label, argv, shown=None, timeout=600, input_text=None):
        """Run a local command (docker exec ...) and append its raw output to `events`."""
        hold_before = hold_exists()
        started = utc_now()
        done = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, input=input_text)
        events.append({
            "kind": "command", "label": label, "command": shown or " ".join(argv),
            "exit_code": done.returncode, "stdout": done.stdout[-6000:], "stderr_tail": done.stderr[-1500:],
            "started_utc": started, "hold_marker_before": hold_before, "hold_marker_after": hold_exists(),
        })
        return done

    def gaps(self):
        return list(self.watch.gaps)


def overlapped_hold(events, gaps_before, gaps_after):
    """True if any event of a gate saw the hold marker, or this process was stopped while the gate ran."""
    seen = any(e.get("hold_marker_before") or e.get("hold_marker_after") for e in events)
    return seen or len(gaps_after) > len(gaps_before)


def state_dir():
    return os.environ.get("GAMMATRON_QUAL_STATE") or os.path.join(os.path.expanduser("~"), ".local", "state", "gammatron-qual")


def load_state(name):
    with open(os.path.join(state_dir(), name)) as f:
        return json.load(f)


def image_pins(refs, platform=None):
    """What `docker image inspect` says about each image that ran, and the digest of the platform manifest
    inside the index that was pulled (looked up on the registry by the index digest), which is the digest the
    sealed list records per platform."""
    pins = {}
    for ref in refs:
        argv = ["docker", "image", "inspect", ref, "--format", "{{json .RepoDigests}}|{{.Id}}|{{.Architecture}}|{{.Os}}"]
        if platform:
            argv[3:3] = ["--platform", platform]
        done = subprocess.run(argv, capture_output=True, text=True)
        if done.returncode != 0:
            pins[ref] = {"error": done.stderr.strip()[-300:]}
            continue
        digests, image_id, arch, os_name = done.stdout.strip().split("|")
        pin = {"repo_digests": json.loads(digests), "image_id": image_id, "architecture": arch, "os": os_name}
        repo = ref.rsplit(":", 1)[0]
        raw = subprocess.run(["docker", "buildx", "imagetools", "inspect", f"{repo}@{image_id}", "--raw"],
                             capture_output=True, text=True)
        try:
            index = json.loads(raw.stdout)
            if "manifests" in index:
                match = [m["digest"] for m in index["manifests"]
                         if m.get("platform", {}).get("architecture") == arch and m.get("platform", {}).get("os") == os_name]
                pin["platform_manifest_digest"] = match[0] if len(match) == 1 else match
            else:  # the pulled digest is itself a single-platform manifest
                pin["platform_manifest_digest"] = image_id
        except ValueError:
            pin["platform_manifest_lookup_error"] = (raw.stderr or raw.stdout).strip()[-300:]
        pins[ref] = pin
    return pins


def write_json(path, value):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(value, f, indent=1)
        f.write("\n")
