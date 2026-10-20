"""Prepared exact LC1056 gate. No provisional policy or candidate execution."""
from pathlib import Path
from . import campaign_1056_transport as transport

need, digest, PROFILE, ENTRY = transport.need, transport.digest, transport.PROFILE, transport.ENTRY
INTERFACE = "exact-public-spelling:lc1056-uint19-to-boolean.v1"
POLICY_SCHEMA = "algsolve.integer1056-admission-policy.v1"
AUTHOR = "/root/normalize_539_541"
REVIEWER = "/root/review_standard"
SOURCE = "0c74b9c1221b37975aa91d3a829915d1d499d9be67f56201f3483bca815318d3"
FREEZE = "8f166eb0988b57526889cab87eca3dbb08007c04a9e7665fe45f53d87f658c3f"
ACTIVATION = "07045360434a3d0eca895e4684d8791ebbd9af7db4f480b6f17c6c49065278b5"
READER = "d7fc8ae6b173062a95071f24e749ad86a0563cea1f383f7910e60f09763edfcb"
DOMAIN = {"minimum": "0", "maximum": "9999999999999999999", "maximum_decimal_digits": 19,
          "safe_number_maximum": "9007199254740991", "javascript_argument": "number-or-bigint",
          "javascript_result": "boolean"}
PIN = {"uid": "lcd:1056", "path": "tests/lcd__1056.json", "tests": 131,
       "sha256": "96e0e8bc4030e1817709887f17ce1b70a622565d68d5d707764b6e097c21bc1c"}
ANCHORS = {
    "freeze": FREEZE,
    "source_interface_freeze": "ca81b178f38f1d1396dd2973fc0cf131cda59c2697e89815076910f4407277bc",
    "handoff": "0adef0b46877ff9e3aea2469428d96065a2cfe69a6843125f36c132796645cd8",
    "technical_review": "b4ea0f6e1a1d176805bfc8fc866fd00a6aa81b5e60576e0a5f1450a306d25bdc",
    "evidence_index": "57d4390b40d64d65277b421eb798930bd85478e39d0fdabeba2949a35ef596db",
    "summary": "c905e938ddcaa51a34754e5fcdaebca0cc02cbe75df25375bdfa9c19423a9979",
    "final_boundary": "154f4aa4e8722a392a4f52fb290956d4e4a39a3580deada493dd7c9ac1870b2b",
    "execution_seal": "53778336444da5d53220fff5422838f6f920e02ae24c8c5f860b7077314f4e99",
    "approved_test_load": "e3c44510ba99c8796eb5b473ccfe0497eaddc1046c8045b737da3881f28a0403",
    "preexecution_review": "52fee32697f14ea617220969a03619987309019534edfa28af1f1828d28efc35",
    "root_approval": "f6339c3471831a7d8106ed9c33c05475b76bcea943b10e93be1d4ec0e12de72e",
    "number_failure": "fc390f2ec263ca32a6fba567f6339804fa1bfefd3b631d6898ca85bd4a50f581",
    "launch_preflight": "ab443e0fcdc5bcb8e237f1a2be98d8d536fbfa3c71ca151e10426f5f611b9510",
    "child_identity": "5c99f6d510eed07dc16b41326080f8ec2411ebbb9da38768de66cc8ace64dd0f",
    "runner_output": "3e32d4c30a653377943a286f6c2ace44ffce24e5805e2ddbf901754c707a03cf",
    "launch_final": "08f46818e0978db68f4a77dfb2564084ab198bc188473caa4794c0ac4d7a86af",
    "runner_exit": "5e6d78127715218225c540f2e05c381767d7048a64049750d191c78bf8d23b3a",
    "packet": "7d1a4eeaf69aac6de2c2714973cdffd2bda21114bbb8572bdb23cd8caf74cea8",
    "standard": "62f20ce3ca6c5b80cb17cb7373db11c214c857e132645390da4790393aac51ea",
    "runtime_contract": "d88b7ab6f128d3f3167b2a5d750a05929d686d2afa506449a869ad1da94c30df",
    "controls": "5b1d0e3a539a8d45621ecc249591f9a8716372813f12fb947b9052aba12495c1",
    "toolchain_manifest": "f20c1b1c358cf1cf29825cd4d3734e6eefcbb724f4a263ad6c87176221a80079",
    "reader_activation": ACTIVATION,
    "historical_reader": READER,
    "source_review": "db9f85deb4cb86e2582dfa246f973ec4e64cc52c0e8fa212706a4cedf40b362e"
}
BINDINGS = tuple(ANCHORS) + ("host_tests",)
MODULES = (
    "campaign_1056_integer.py", "campaign_1056_replay.py", "campaign_1056_transport.py",
    "campaign_868_dispatch.py", "campaign_868_integer.py", "campaign_868_replay.py",
    "campaign_868_transition.py", "campaign_738_integer.py", "campaign_uint1024_dispatch.py",
    "campaign_integer_dispatch.py", "campaign_633_integer.py", "campaign_exact_integer.py",
    "campaign_toolchain.py", "corpus_campaign.py")


def identity(value):
    return type(value) is str and value == value.strip() and bool(value)


def key(entry):
    need(type(entry) is dict and type(entry.get("id")) is int and
         type(entry.get("language")) is str, "Exact entry identity required")
    return f"{entry['id']:04d}:{entry['language']}"


def read(reference):
    """Hash and decode the same retained bytes; never hash then reopen for JSON."""
    need(type(reference) is dict and type(reference.get("path")) is str and
         type(reference.get("sha256")) is str and
         len(reference["sha256"]) == 64, "Exact reference required")
    path = Path(reference["path"])
    need(path.is_absolute(), "Absolute artifact reference required")
    raw = path.read_bytes()
    need(transport.sha(raw) == reference["sha256"], "Artifact hash differs")
    return raw


def check(reference):
    return transport.parse(read(reference))


def policy(data):
    reference = data.get("inputs", {}).get("integer1056_policy")
    if reference is None:
        return None, None
    value = check(reference)
    need(value.get("schema") == POLICY_SCHEMA and type(value.get("entries")) is dict and
         set(value["entries"]) == {ENTRY}, "1056 policy must contain only1056JavaScript")
    return reference, value


def requires_profile(data, entry):
    reference, value = policy(data)
    return value is not None and key(entry) in value["entries"]


def metadata(value, entry, contract):
    """Pure metadata checks, separately testable without opening qualification files."""
    need(key(entry) == ENTRY and entry.get("key") == "lc:confusing-number",
         "Only1056JavaScript confusingNumber supported")
    need(contract.get("schema") == "algsolve.campaign-contract.v3" and
         contract.get("interface") == INTERFACE and contract.get("comparison") == "unchanged" and
         not any(k in contract for k in ("public_comparison", "independent_comparison")),
         "Exact1056 interface and unchanged comparisons required")
    need(value is not None and value.get("schema") == POLICY_SCHEMA and
         value.get("status") == "approved" and value.get("approved_by") == "/root" and
         type(value.get("entries")) is dict and set(value["entries"]) == {ENTRY},
         "Explicit coordinator-approved1056 policy required")
    allowed = value["entries"][ENTRY]
    need(type(allowed) is dict and allowed.get("source_author") == AUTHOR and
         contract.get("source_author") == AUTHOR and
         identity(allowed.get("technical_reviewer")) and allowed["technical_reviewer"] == REVIEWER and
         len({AUTHOR, REVIEWER, value["approved_by"]}) == 3,
         "Distinct named source author, technical reviewer and approver required")
    need(allowed.get("profile") == PROFILE and digest(allowed.get("numeric_domain")) == digest(DOMAIN) and
         allowed.get("normalized_sha256") == contract.get("normalized_sha256") == SOURCE,
         "Unreviewed1056 source/profile/domain")
    need(type(contract.get("public_tests")) is int and contract["public_tests"] == 3 and
         digest(entry.get("independent_sets")) == digest([PIN]), "Exact unchanged134 cases required")
    for name, wanted in ANCHORS.items():
        need(type(allowed.get(name)) is dict and allowed[name].get("sha256") == wanted,
             "Unreviewed1056 anchor: " + name)
    need(contract.get("standard_sha256") == ANCHORS["standard"], "Checker policy differs")
    return allowed


def descriptor(reference, allowed):
    return {"profile": PROFILE, "entry": ENTRY, "numeric_domain": DOMAIN,
            "policy_sha256": reference["sha256"],
            "bindings": {name: allowed[name]["sha256"] for name in BINDINGS},
            "runtime": allowed["runtime"]}


def module_hashes():
    root = Path(__file__).parent
    return {name: transport.sha((root / name).read_bytes()) for name in MODULES}


def profile(data, entry, contract):
    reference, value = policy(data)
    allowed = metadata(value, entry, contract)
    need(allowed.get("admission_modules") == module_hashes(), "1056 module closure drift")
    bound, refs = {}, [reference]
    for name in BINDINGS:
        item = allowed.get(name)
        raw = read(item)
        bound[name] = raw.decode() if name in ("historical_reader", "number_failure") else transport.parse(raw)
        refs.append(item)
    frozen = bound["freeze"]
    need(frozen.get("schema") == "algsolve.integer1056-claim-bound-runtime-freeze.v1" and
         frozen.get("stage") == "claim-bound-execution-candidate" and
         frozen.get("entry") == ENTRY and frozen.get("profile") == PROFILE,
         "Exact claim-bound qualification freeze required")
    root = Path(allowed["freeze"]["path"]).parent
    need(len(frozen["sources"]) == 178 and len(frozen["host_dependencies"]) == 114,
         "Frozen runtime closure incomplete")
    for relative, wanted in frozen["sources"].items():
        path = root / relative
        need(not Path(relative).is_absolute() and ".." not in Path(relative).parts,
             "Frozen source escaped batch")
        item = {"path": str(path), "sha256": wanted}
        read(item); refs.append(item)
    for item in frozen["host_dependencies"] + frozen["authority_dependencies"]:
        read(item); refs.append(item)
    need(frozen["sources"]["candidate.js"] == SOURCE and
         frozen["sources"]["codec.py"] == "86f8c904304aadb724eb9c82840b5da52cf5387971df974e3e2f65d4e845cda8" and
         frozen["sources"]["harness.cjs"] == "4f6bf8608e798e213258142388ef6dd18be227a13e24d633d386aae767094d58" and
         frozen["sources"]["harness.py"] == "7bdf97d39c0ca4bac1ab7cde89d3f9007ed6959b7db3f3662809be6341766b66",
         "Source/codec/harness changed")
    source_freeze = bound["source_interface_freeze"]
    need(frozen.get("source_interface_freeze_sha256") == ANCHORS["source_interface_freeze"] and
         source_freeze.get("entry") == ENTRY and source_freeze.get("profile") == PROFILE and
         source_freeze.get("files", {}).get("candidate.js") == SOURCE and
         source_freeze["files"].get("policy.json") == ANCHORS["standard"] and
         source_freeze["files"].get("contract.json") == ANCHORS["runtime_contract"],
         "Source/interface checker freeze differs")
    for field, relative in (("packet", "1056-packet.json"), ("controls", "execution-controls.json"),
                            ("toolchain_manifest", "toolchain-manifest.json")):
        need(frozen["sources"][relative] == allowed[field]["sha256"], "Freeze binding differs")
    review = bound["technical_review"]
    need(review.get("schema") == "algsolve.exact-integer-profile-independent-review.v2" and
         review.get("runtime_qualification_status") == "passed" and review.get("entry") == ENTRY and
         review.get("runtime_profile") == PROFILE and review.get("author") == AUTHOR and
         review.get("reviewer") == REVIEWER and review.get("freeze", {}).get("sha256") == FREEZE,
         "Named passing independent technical replay required")
    reviewed_sources = review.get("sources")
    need(type(reviewed_sources) is dict and reviewed_sources.get("candidate.js", {}).get("sha256") == SOURCE,
         "Source not independently reviewed")
    reviewed = {(r["path"], r["sha256"]) for r in review.get("evidence", [])}
    critical = ("evidence_index", "summary", "final_boundary", "execution_seal", "approved_test_load",
                "preexecution_review", "root_approval", "launch_preflight", "child_identity",
                "runner_output", "launch_final", "runner_exit")
    need(all((allowed[n]["path"], allowed[n]["sha256"]) in reviewed for n in critical),
         "Technical review does not bind complete execution/lifecycle evidence")
    need(review.get("handoff") == allowed["handoff"], "Technical handoff differs")
    for item in list(reviewed_sources.values()) + review.get("evidence", []):
        read(item); refs.append(item)
    approval = bound["root_approval"]
    need(approval.get("status") == "approved" and approval.get("approved_by") == "/root" and
         approval.get("purpose") == "1056-exact-integer-qualification" and
         approval.get("freeze_sha256") == FREEZE, "Exact execution approval missing")
    packet = bound["packet"]
    need(packet.get("id") == 1056 and packet.get("key") == entry["key"] and
         packet.get("entry") == {"class": "Solution", "method": "confusingNumber"} and
         packet.get("params") == [["n", "int"]] and
         digest(packet.get("independent_test_sets")) == digest([PIN]), "Public adapter identity differs")
    groups = bound["host_tests"]
    need(type(groups) is list and [g.get("name") for g in groups] == ["public", "independent-lcd-1056"] and
         len(groups[0]["tests"]) == 3 and len(groups[1]["tests"]) == 131 and
         digest(groups[0]["tests"]) == digest(packet["public_tests"]) and
         digest(groups[1]["tests"]) == PIN["sha256"], "Unchanged host test groups required")
    test_load = bound["approved_test_load"]
    need(test_load.get("schema") == "algsolve.approved-test-load.v1" and
         test_load.get("uid") == PIN["uid"] and test_load.get("relative_path") == PIN["path"] and
         type(test_load.get("tests")) is int and test_load["tests"] == 131 and
         test_load.get("sha256") == PIN["sha256"] and
         test_load.get("raw_sha256") == "e274b17d2e5112f2f0d3de2194480272291c4f25425e031d6195ed44b76fc1ee" and
         test_load.get("comparison") == "unchanged" and test_load.get("corrections_applied") is False and
         test_load.get("host_only") is True, "Exact scoped host test-load proof required")
    for case in groups[0]["tests"] + groups[1]["tests"]:
        transport.encode_calls([case])
        need(type(case.get("expected")) is bool and case.get("compare", "return") == "return",
             "Strict original Boolean comparison required")
    from . import campaign_exact_integer as common, campaign_toolchain
    need(allowed.get("runtime") == {n: common.sha(p) for n, p in common.RUNTIME.items()},
         "Trusted host judge drift")
    refs += [common.ref(p) for p in common.RUNTIME.values()]
    campaign_toolchain.verify(bound["toolchain_manifest"])
    predecessor = review.get("preserved_predecessor", {})
    need(predecessor.get("opaque_inventory") == allowed["number_failure"] and
         predecessor.get("historical_result") == "133/134 functional returns; one wrong result and three wide Number input roundtrip failures outside official range, as previously independently reviewed in Round18.",
         "Historical Number failure inventory must remain linked without rescoring or relabeling")
    expected = descriptor(reference, allowed)
    need(digest(contract.get("runtime_profile")) == digest(expected), "Runtime descriptor differs")
    bound["_root"], bound["_allowed"] = root, allowed
    return expected, bound, refs


def execution_profile(data, entry, contract, execution, review):
    expected, bound, refs = profile(data, entry, contract)
    need(digest(execution.get("runtime_profile")) == digest(expected) ==
         digest(review.get("runtime_profile")) and review.get("reviewer") == REVIEWER and
         review.get("runtime_profile_reviewed") is True and
         review.get("runtime_qualification_sha256") == bound["_allowed"]["technical_review"]["sha256"],
         "Named independent admission review and exact descriptor required")
    from .campaign_1056_replay import replay
    totals = replay(bound, refs)
    need(totals == {"cases_each": 134, "passed_each": 134, "calls": 118, "controls": 49},
         "Complete1056 qualification required")
    for name, wanted in {"public_total": 3, "public_passed": 3, "independent_total": 131,
                         "independent_passed": 131, "infrastructure_errors": 0, "decoding_errors": 0}.items():
        need(type(execution.get(name)) is int and execution[name] == wanted, "Execution count differs")
    declared = {(r["path"], r["sha256"]) for r in execution.get("artifacts", [])}
    need(all((r["path"], r["sha256"]) in declared for r in refs), "Receipt omits qualification closure")
    return refs
