"""Shared helpers for the iu1-b screen cases. Standard library only.

Environment:
  SCREEN_HOLD_FILE  path of the HOLD marker of the machine's measurement session (optional)
  SCREEN_SCRATCH    directory for generated passwords and unredacted evidence (required)

Nothing here writes a password, token or key into the repository: every generated or
application-issued secret is registered with add_secret() and replaced by <redacted>
when a result file is written.
"""
import json
import os
import re
import secrets as _secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request

LABEL = "gammatron-screen=iu1-b"
HOLD_FILE = os.environ.get("SCREEN_HOLD_FILE", "")
SCRATCH = os.environ.get("SCREEN_SCRATCH", "")
SECRETS = set()
JWT_RE = re.compile(r"eyJ[A-Za-z0-9_-]{8,}(?:\.[A-Za-z0-9_-]*)*")  # also a token cut short by an excerpt


def log(*parts):
    print(time.strftime("%H:%M:%S", time.gmtime()), *parts, file=sys.stderr, flush=True)


def utc_now():
    """UTC time from the system clock via `date -u`."""
    return subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip()


def new_secret(nbytes=18):
    value = _secrets.token_hex(nbytes)
    SECRETS.add(value)
    return value


def add_secret(value):
    if isinstance(value, str) and len(value) >= 6:
        SECRETS.add(value)
    return value


def redact_text(text):
    for value in sorted(SECRETS, key=len, reverse=True):
        text = text.replace(value, "<redacted>")
    return JWT_RE.sub("<redacted>", text)


def redact(obj):
    return json.loads(redact_text(json.dumps(obj)))


# ---------------------------------------------------------------- hold rule

def _hold_dir_state():
    if not HOLD_FILE:
        return None
    base = os.path.dirname(HOLD_FILE)
    state = [os.path.exists(HOLD_FILE)]
    for name in ("stopped-pids.txt", "paused-containers.txt"):
        try:
            state.append(os.stat(os.path.join(base, name)).st_mtime_ns)
        except OSError:
            state.append(None)
    return state


def hold_active():
    return bool(HOLD_FILE) and os.path.exists(HOLD_FILE)


def wait_hold():
    """Start nothing while the HOLD file exists; check every 30 seconds."""
    waited = 0
    while hold_active():
        if waited == 0:
            log("HOLD present, waiting")
        time.sleep(30)
        waited += 30
    if waited:
        log("HOLD gone after about %d s" % waited)
    return waited


class HoldWatch:
    """Detects a hold that overlapped a span of work.

    A hold touches the marker file and rewrites two side files, and it may stop this
    process as well, so the check compares the state before and after the span.
    """

    def __init__(self):
        wait_hold()
        self.before = _hold_dir_state()
        self.started = utc_now()

    def overlapped(self):
        after = _hold_dir_state()
        if after is None:
            return False
        return after[0] or after != self.before

    def record(self):
        return {"checked_before_utc": self.started, "checked_after_utc": utc_now(),
                "hold_overlapped": self.overlapped(), "hold_file_configured": bool(HOLD_FILE)}


# ---------------------------------------------------------------- docker

def sh(args, check=True, input_text=None, timeout=900):
    proc = subprocess.run(args, input=input_text, capture_output=True, text=True, timeout=timeout)
    if check and proc.returncode != 0:
        raise RuntimeError("command failed (%d): %s\n%s" % (
            proc.returncode, redact_text(" ".join(args))[:400], redact_text(proc.stderr)[-1500:]))
    return proc


def docker(*args, **kw):
    return sh(["docker", *args], **kw)


def case_label(case):
    return "iu1-b-case=%s" % case


def teardown(case):
    """Remove this case's containers, volumes and networks, selected by label only."""
    flt = ["--filter", "label=" + LABEL, "--filter", "label=" + case_label(case)]
    ids = docker("ps", "-aq", *flt).stdout.split()
    if ids:
        docker("rm", "-f", "-v", *ids, check=False)
    vols = docker("volume", "ls", "-q", *flt).stdout.split()
    if vols:
        docker("volume", "rm", "-f", *vols, check=False)
    nets = docker("network", "ls", "-q", *flt).stdout.split()
    if nets:
        docker("network", "rm", *nets, check=False)


def network_create(case, name):
    docker("network", "create", "--label", LABEL, "--label", case_label(case), name)


def volume_create(case, name):
    docker("volume", "create", "--label", LABEL, "--label", case_label(case), name)


def run_container(case, name, image, env=None, publish=None, network=None, alias=None,
                  mounts=None, extra=None, cmd=None):
    """publish: list of (host_port, container_port); always bound to 127.0.0.1."""
    args = ["run", "-d", "--name", name, "--label", LABEL, "--label", case_label(case)]
    if network:
        args += ["--network", network]
        if alias:
            args += ["--network-alias", alias]
    for host_port, cont_port in (publish or []):
        if not 28610 <= int(host_port) <= 28699:
            raise ValueError("port outside the lane's range")
        args += ["-p", "127.0.0.1:%d:%d" % (host_port, cont_port)]
    for key, value in (env or {}).items():
        args += ["-e", "%s=%s" % (key, value)]
    for mount in (mounts or []):
        args += ["-v", mount]
    args += list(extra or [])
    args.append(image)
    args += list(cmd or [])
    return docker(*args).stdout.strip()


def pull_pinned(repo, digest):
    """Pull by digest and return what `docker image inspect` reports."""
    ref = "%s@%s" % (repo, digest)
    if docker("image", "inspect", ref, check=False).returncode != 0:
        wait_hold()
        log("pulling", ref)
        docker("pull", ref, timeout=3600)
    info = json.loads(docker("image", "inspect", ref).stdout)[0]
    return {"pulled_ref": ref, "inspect_id": info.get("Id"), "repo_digests": info.get("RepoDigests"),
            "architecture": info.get("Architecture"), "os": info.get("Os"),
            "created": info.get("Created"), "size_bytes": info.get("Size")}


def tag_resolves_today(ref, arch):
    """What the registry serves for this tag and platform now (tags can be re-pushed)."""
    proc = docker("buildx", "imagetools", "inspect", ref, "--raw", check=False, timeout=120)
    try:
        doc = json.loads(proc.stdout)
    except ValueError:
        return None
    for manifest in doc.get("manifests", []):
        plat = manifest.get("platform", {})
        if plat.get("architecture") == arch and plat.get("os") == "linux":
            return manifest.get("digest")
    return None


def pin_images(sealed, refs):
    """refs: list of (sealed ref, repository). Pull each by the sealed digest and record it."""
    pins, images = {}, []
    for ref, repo in refs:
        arch, digest = sealed_digest(sealed, ref)
        pin = pull_pinned(repo, digest)
        pins[ref] = pin
        today = tag_resolves_today(ref, arch)
        images.append({
            "ref": ref, "sealed_platform": arch, "sealed_digest": digest, **pin,
            "pulled_digest_equals_sealed": any(d.endswith(digest) for d in pin["repo_digests"] or []),
            "tag_resolves_today_to": today,
            "tag_today_equals_sealed": (today == digest) if today else None})
    return pins, images


def memory_snapshot():
    out = docker("stats", "--no-stream", "--format", "{{.Name}}\t{{.MemUsage}}", check=False).stdout
    return [line for line in out.splitlines() if line.strip()]


def free_disk_gib(path=None):
    stat = os.statvfs(path or os.path.expanduser("~"))
    return round(stat.f_bavail * stat.f_frsize / 2 ** 30, 1)


# ---------------------------------------------------------------- http

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def http(method, url, body=None, headers=None, timeout=60, raw=None, follow=True):
    """One request. Returns (status, text, response_headers). Never raises on HTTP status."""
    data = None
    hdrs = dict(headers or {})
    if raw is not None:
        data = raw if isinstance(raw, bytes) else raw.encode()
    elif body is not None:
        data = json.dumps(body).encode()
        hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace"), dict(resp.headers)
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8", "replace"), dict(err.headers)


class Recorder:
    """Collects every request of one repeat as raw evidence."""

    def __init__(self, base_url):
        self.base = base_url.rstrip("/")
        self.calls = []

    def call(self, step, method, path, body=None, headers=None, raw=None, excerpt=1200, timeout=60):
        started = utc_now()
        try:
            status, text, _ = http(method, self.base + path, body=body, headers=headers, raw=raw,
                                   timeout=timeout)
            error = None
        except Exception as exc:  # connection refused, timeout
            status, text, error = None, "", "%s: %s" % (type(exc).__name__, exc)
        entry = {
            "step": step, "utc": started, "method": method, "path": path,
            "request_body": body if raw is None else (raw if isinstance(raw, str) else "<bytes>"),
            "request_header_names": sorted((headers or {}).keys()),
            "status": status, "response_body_excerpt": text[:excerpt],
            "response_body_length": len(text),
        }
        if error:
            entry["transport_error"] = error
        self.calls.append(entry)
        parsed = None
        try:
            parsed = json.loads(text)
        except ValueError:
            pass
        return status, parsed, text


def wait_http(url, ok=lambda status, text: status == 200, timeout=900, interval=5, headers=None):
    """Poll until the application answers. Time spent in a hold does not count."""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        deadline += wait_hold()
        try:
            status, text, _ = http("GET", url, headers=headers, timeout=20)
            last = (status, text[:200])
            if ok(status, text):
                return True
        except Exception as exc:
            last = (None, str(exc)[:200])
        time.sleep(interval)
    raise RuntimeError("not ready after %d s: %s last=%r" % (timeout, url, last))


# ---------------------------------------------------------------- repeats

def run_repeat(case, fn, repeat, max_attempts=5):
    """Run one repeat on an instance started from nothing.

    fn(repeat) returns a dict with a list "observations"; each observation carries a
    "hold" record from HoldWatch.record(). An observation that overlapped a hold is void:
    the whole repeat is discarded and run again on a fresh instance.
    """
    voided = []
    for attempt in range(1, max_attempts + 1):
        wait_hold()
        teardown(case)
        try:
            evidence = fn(repeat)
        finally:
            teardown(case)
        overlapped = [o.get("gate") for o in evidence.get("observations", [])
                      if o.get("hold", {}).get("hold_overlapped")]
        if overlapped:
            log("repeat %d attempt %d void: hold overlapped %s" % (repeat, attempt, overlapped))
            voided.append({"attempt": attempt, "void_because_hold_overlapped": overlapped,
                           "utc": utc_now()})
            continue
        evidence["attempt"] = attempt
        evidence["voided_attempts"] = voided
        return evidence
    raise RuntimeError("repeat %d: every attempt overlapped a hold" % repeat)


# ---------------------------------------------------------------- results

def write_json(path, obj, redacted=True):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    if redacted:
        text = redact_text(text)
        json.loads(text)
    tmp = path + ".tmp"
    with open(tmp, "w") as handle:
        handle.write(text)
    os.replace(tmp, path)


def scratch_dir(case):
    if not SCRATCH:
        raise SystemExit("set SCREEN_SCRATCH to a directory outside the repository")
    path = os.path.join(SCRATCH, case)
    os.makedirs(path, exist_ok=True)
    return path


def sealed_case(case_id):
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "..", "..", "screen-list.json")) as handle:
        doc = json.load(handle)
    for cand in doc["candidates"]:
        if cand["id"] == case_id:
            return cand
    raise KeyError(case_id)


def sealed_digest(case, ref, arch="arm64"):
    for image in case["images"]:
        if image["ref"] == ref:
            plats = image["platforms"]
            use = arch if arch in plats else "amd64"
            return use, plats[use]["digest"]
    raise KeyError(ref)
