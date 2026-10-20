"""Prepared exact LC989 gate. No provisional policy or candidate execution."""
from pathlib import Path
from . import campaign_989_transport as transport

need, digest, PROFILE, ENTRY = transport.need, transport.digest, transport.PROFILE, transport.ENTRY
INTERFACE = "exact-public-spelling:" + PROFILE
POLICY_SCHEMA = "algsolve.integer989-admission-policy.v1"
AUTHOR = "/root/normalize_539_541"
REVIEWER = "/root/review_standard"
SOURCE = '5ce2ab70c9b3023e6111a58232b0909c59a31006662eee36f5b01f80c3828973'
FREEZE = '00d245a06f011a33f2883833f9c078307a66c22c8a14d2c15617c8178d9df91c'
ACTIVATION = '564f1da6ddedfbb570de1ec76ab18f6291b17d8cf2cf9785561c30007d386ea0'
READER = 'd7fc8ae6b173062a95071f24e749ad86a0563cea1f383f7910e60f09763edfcb'
DOMAIN = {'array_maximum_length': 10000, 'array_minimum_length': 1, 'carry_maximum_decimal': '99999999999999999999999999999999999999999999999', 'carry_maximum_decimal_digits': 47, 'carry_minimum': 1, 'digit_maximum': 9, 'digit_minimum': 0, 'leading_zero_arrays_allowed': True, 'output_elements': 'exact Number integers0..9', 'output_maximum_length': 10001, 'output_minimum_length': 1}
PIN = {'uid': 'lcd:989', 'tests': 75, 'sha256': '41678d59219fde9339b6ff835fb0461e99fe10455dfe82b845805407c21a3978', 'path': 'tests/lcd__989.json'}
ANCHORS = {'freeze': '00d245a06f011a33f2883833f9c078307a66c22c8a14d2c15617c8178d9df91c', 'source_interface_freeze': 'd4ab9f8f6b897259d8955406f8a0051ab9ee23ad696bd66cc4db4247df88a747', 'handoff': '263e76abdee8241a1f44e020a7f7862d154be3ec9acc78f63548f703a6355ab4', 'technical_review': '9f644f97a0d7e7d44043c05335b2b23c0d6ad89796a0248d8e4ac1f7a5bad994', 'evidence_index': '0f341e2d27c620854f043fce4728e6435071dceaa71e339c8ffca96adf6786da', 'summary': '61c07be9d9d7a779980f9c8fc1fef8bf2d2754bd5fb98625ccc8b594cb10a365', 'final_boundary': 'df81dae06fdf37146d1662c722564d6a053e6e6b194467f6e9fce9deafc1d91a', 'execution_seal': 'e1f8d72093cece5f40fb5fab5a69fd931a457baeace32f513d45f65f0eaddfe2', 'approved_test_load': '25b78355c51bb26232174f7ca1fcc9a192086895aa71111a5cc74bcf23940d6d', 'preexecution_review': 'd3aea964adb56d5dbc60e955ad4df273ed81a4a2e998bff10b1e50e050a23c34', 'root_approval': 'fa176c7c4d7c13bfdec1ed586ec60c461eaebbc49395e42d37280f03cc5908fe', 'number_failure': 'bd764eb2ae144d1c2045221b9d6d16ef49ff04c76008706561d7fcc450f290ca', 'launch_preflight': '5da733b40472614ecb16c1441d5b9f51ef92416798bfe65b71180e5518bce04a', 'child_identity': 'f6f0785e2192dbfee8dcc89d42f81fdacf274acce4233b01d4443b03bbd3a9c7', 'runner_output': '4f09d9c1044326ae94abb26a78ed6d19188dca9c391407e977d545febea1de23', 'launch_final': 'ad201aaa8ac33267ebe7e2bdc3fbcc287b92332f1a622f64e21dfb7089da94a9', 'runner_exit': '2f04d82561784ffafc768ba468fc2f73e286cf45445cc4860148ea87191bceb2', 'packet': 'b338b0ed8dd8e19b7729d30f5a1c1187510faf5bd5cad6cb7cff287197c09861', 'standard': '034c911ef047368f71851ae68b8281bb2b81ae8f03aace73334415bb3780c852', 'standard_predecessor': '6337939ea35c8a743f3b911bde722aca9a75fa7ad4bd630438c8af44ee794867', 'standard_result': '7d3524d8451f14f3efbdd36ab23769dd8ae280408e9eaf0d65b3d05b3903fd49', 'standard_mapping': 'b78e55c6b42801eee85ca6793e9694e7c647042743b0b1086a6c5fffb874032b', 'standard_checker': 'ed85cf0bad1f9b44d8050c3fbf3eab9d2ad2fad5b95afdd9aafde4ef483d10e2', 'runtime_contract': '84e54b3ba155885c310e816c51adc0bbadd13bce6f474076d60ce846fe5cf2e9', 'controls': '98c1d604646726272733e2ddfb11048ef4ef5a9774fc528e3f424ddba7b0b786', 'toolchain_manifest': 'c41e0fce38492de547c207d191d34dc6553718f2e65ef44e5650125ef38c938e', 'reader_activation': '564f1da6ddedfbb570de1ec76ab18f6291b17d8cf2cf9785561c30007d386ea0', 'historical_reader': 'd7fc8ae6b173062a95071f24e749ad86a0563cea1f383f7910e60f09763edfcb', 'source_review': 'b9d55e3078229ab2bb7bd388aee2210b67cc1a9f2e100d9f1e14cad2e05fac34', 'outer_launcher': 'b996b07890aa1ab3b8f1e256a29c24c6ff9e4e76a1336cbfe4bcd86e1bb7f1dc', 'outer_launch': '12ff48783416aff70785b2b3e6a143e861c243777534b1c9686b022dbc8c698c'}
HOST_TESTS_SHA = 'cf96f890fa27cec4c898f07ea53a45436dd9842d8be8039b5d14e86da9070159'
BINDINGS = tuple(ANCHORS) + ("host_tests",)
MODULES = (
    "campaign_989_integer.py", "campaign_989_replay.py", "campaign_989_transport.py",
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
    reference = data.get("inputs", {}).get("integer989_policy")
    if reference is None:
        return None, None
    value = check(reference)
    need(value.get("schema") == POLICY_SCHEMA and type(value.get("entries")) is dict and
         set(value["entries"]) == {ENTRY}, "989 policy must contain only989JavaScript")
    return reference, value


def requires_profile(data, entry):
    reference, value = policy(data)
    return value is not None and key(entry) in value["entries"]


def metadata(value, entry, contract):
    """Pure metadata checks, separately testable without opening qualification files."""
    need(key(entry) == ENTRY and entry.get("key") == "lc:add-to-array-form-of-integer",
         "Only989JavaScript addToArrayForm supported")
    need(contract.get("schema") == "algsolve.campaign-contract.v3" and
         contract.get("interface") == INTERFACE and contract.get("comparison") == "unchanged" and
         not any(k in contract for k in ("public_comparison", "independent_comparison")),
         "Exact989 interface and unchanged comparisons required")
    need(value is not None and value.get("schema") == POLICY_SCHEMA and
         value.get("status") == "approved" and value.get("approved_by") == "/root" and
         type(value.get("entries")) is dict and set(value["entries"]) == {ENTRY},
         "Explicit coordinator-approved989 policy required")
    allowed = value["entries"][ENTRY]
    need(type(allowed) is dict and allowed.get("source_author") == AUTHOR and
         contract.get("source_author") == AUTHOR and
         identity(allowed.get("technical_reviewer")) and allowed["technical_reviewer"] == REVIEWER and
         len({AUTHOR, REVIEWER, value["approved_by"]}) == 3,
         "Distinct named source author, technical reviewer and approver required")
    need(allowed.get("profile") == PROFILE and digest(allowed.get("numeric_domain")) == digest(DOMAIN) and
         allowed.get("normalized_sha256") == contract.get("normalized_sha256") == SOURCE,
         "Unreviewed989 source/profile/domain")
    need(type(contract.get("public_tests")) is int and contract["public_tests"] == 3 and
         digest(entry.get("independent_sets")) == digest([PIN]), "Exact unchanged78 cases required")
    for name, wanted in ANCHORS.items():
        need(type(allowed.get(name)) is dict and allowed[name].get("sha256") == wanted,
             "Unreviewed989 anchor: " + name)
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
    need(digest(allowed.get("admission_modules")) == digest(module_hashes()), "989 module closure drift")
    bound, refs = {}, [reference]
    for name in BINDINGS:
        item = allowed.get(name)
        raw = read(item)
        bound[name] = raw.decode() if name in ("historical_reader", "number_failure", "outer_launcher", "standard_checker") else transport.parse(raw)
        refs.append(item)
    frozen = bound["freeze"]
    need(frozen.get("schema") == "algsolve.integer989-claim-bound-runtime-freeze.v1" and
         frozen.get("stage") == "claim-bound-execution-candidate" and
         frozen.get("entry") == ENTRY and frozen.get("profile") == PROFILE,
         "Exact claim-bound qualification freeze required")
    root = Path(allowed["freeze"]["path"]).parent
    need(len(frozen["sources"]) == 92 and len(frozen["host_dependencies"]) == 115,
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
         frozen["sources"]["codec.py"] == "c39bf38e2affd318573c6e148cf20657760ce0d060de908acbb5235b9c9d11a2" and
         frozen["sources"]["harness.cjs"] == "6d77961cfc16ddb4eb5f85a2449cf001c5e38424d0cc5d65ac6a7422de291b37",
         "Source/codec/harness changed")
    standard = bound["standard"]
    need(standard.get("candidate_sha256") == SOURCE and
         standard.get("extra_global_allowance") == ["BigInt", "Number"] and
         bound["standard_result"].get("errors") == [] and
         transport.sha(bound["standard_result"].get("formatted", "")) == SOURCE and
         bound["standard_mapping"].get("source_sha256") == SOURCE and
         bound["standard_mapping"].get("reviewed_by") == AUTHOR,
         "Exact local source standard proof required")
    source_freeze = bound["source_interface_freeze"]
    source_files = {Path(v["path"]).name: v["sha256"] for v in source_freeze["files"]}
    need(source_freeze.get("entry") == ENTRY and source_freeze.get("profile") == PROFILE and
         source_files.get("candidate.js") == SOURCE and source_files.get("policy-local-proposal.json") == ANCHORS["standard_predecessor"] and
         source_files.get("contract.json") == ANCHORS["runtime_contract"], "Source interface freeze differs")
    for field, relative in (("packet", "989-packet.json"), ("controls", "controls.json"),
                            ("toolchain_manifest", "toolchain-manifest.json")):
        need(frozen["sources"][relative] == allowed[field]["sha256"], "Freeze binding differs")
    review = bound["technical_review"]
    need(review.get("schema") == "algsolve.exact-integer-profile-independent-review.v2" and
         review.get("runtime_qualification_status") == "passed" and review.get("entry") == ENTRY and
         review.get("runtime_profile") == PROFILE and review.get("author") == AUTHOR and
         review.get("reviewer") == REVIEWER and review.get("freeze", {}).get("sha256") == FREEZE,
         "Named passing independent technical replay required")
    reviewed_sources = review.get("sources")
    need(type(reviewed_sources) is dict and reviewed_sources.get("javascript", {}).get("sha256") == SOURCE,
         "Source not independently reviewed")
    reviewed = {(r["path"], r["sha256"]) for r in review.get("evidence", [])}
    critical = ("evidence_index", "summary", "final_boundary", "execution_seal", "approved_test_load",
                "preexecution_review", "root_approval", "launch_preflight", "child_identity",
                "runner_output", "launch_final", "runner_exit")
    need(all((allowed[n]["path"], allowed[n]["sha256"]) in reviewed for n in critical),
         "Technical review does not bind complete execution/lifecycle evidence")
    need((allowed["handoff"]["path"], allowed["handoff"]["sha256"]) in reviewed, "Technical handoff differs")
    for item in list(reviewed_sources.values()) + review.get("evidence", []):
        read(item); refs.append(item)
    approval = bound["root_approval"]
    need(approval.get("status") == "approved" and approval.get("approved_by") == "/root" and
         approval.get("purpose") == "989-exact-integer-qualification" and
         approval.get("freeze_sha256") == FREEZE, "Exact execution approval missing")
    packet = bound["packet"]
    need(packet.get("id") == 989 and packet.get("key") == entry["key"] and
         packet.get("entry") == {"class": "Solution", "method": "addToArrayForm"} and
         packet.get("params") == [["num", "List[int]"], ["k", "int"]] and
         digest(packet.get("independent_test_sets")) == digest([PIN]), "Public adapter identity differs")
    envelope = bound["host_tests"]
    need(allowed["host_tests"]["sha256"] == HOST_TESTS_SHA and
         envelope.get("schema") == "algsolve.private-host-test-groups.v1" and envelope.get("comparison") == "unchanged",
         "Exact private host expectation envelope required")
    groups = [{"name": "public", "tests": envelope["groups"]["public"]},
              {"name": "independent-lcd-989", "tests": envelope["groups"]["independent:lcd:989"]}]
    need(set(envelope["groups"]) == {"public", "independent:lcd:989"} and
         len(groups[0]["tests"]) == 3 and len(groups[1]["tests"]) == 75 and
         digest(groups[0]["tests"]) == digest(packet["public_tests"]) and
         digest(groups[1]["tests"]) == PIN["sha256"], "Unchanged host test groups required")
    bound["_groups"] = groups
    test_load = bound["approved_test_load"]
    need(test_load.get("schema") == "algsolve.approved-test-load.v1" and
         test_load.get("uid") == PIN["uid"] and test_load.get("relative_path") == PIN["path"] and
         type(test_load.get("tests")) is int and test_load["tests"] == 75 and
         test_load.get("sha256") == PIN["sha256"] and
         test_load.get("raw_sha256") == "6ad2ae927fa34afcbc01d1e0fd747dd0ada76a7bf0dfe5f037d8a27fb775ffbd" and
         test_load.get("comparison") == "unchanged" and test_load.get("corrections_applied") is False and
         test_load.get("host_only") is True, "Exact scoped test-load proof required")
    for case in groups[0]["tests"] + groups[1]["tests"]:
        transport.encode_calls([case]); transport.digits(case.get("expected"), 10001)
        need(case.get("compare", "return") == "return", "Strict original sequence comparison required")
    from . import campaign_exact_integer as common, campaign_toolchain
    need(allowed.get("runtime") == {n: common.sha(p) for n, p in common.RUNTIME.items()},
         "Trusted host judge drift")
    refs += [common.ref(p) for p in common.RUNTIME.values()]
    campaign_toolchain.verify(bound["toolchain_manifest"])
    need(review.get("admission_authorized") is False and review.get("candidate_reruns") == 0 and
         review.get("unresolved_findings") == [], "Technical review scope differs")
    need(bound["handoff"].get("preserved_prior_failure", "").startswith("Native Number71/78 retained"),
         "Historical Number failure must remain explicit")
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
    from .campaign_989_replay import replay
    totals = replay(bound, refs)
    need(totals == {"cases_each": 78, "passed_each": 78, "calls": 39, "controls": 18},
         "Complete989 qualification required")
    for name, wanted in {"public_total": 3, "public_passed": 3, "independent_total": 75,
                         "independent_passed": 75, "infrastructure_errors": 0, "decoding_errors": 0}.items():
        need(type(execution.get(name)) is int and execution[name] == wanted, "Execution count differs")
    declared = {(r["path"], r["sha256"]) for r in execution.get("artifacts", [])}
    need(all((r["path"], r["sha256"]) in declared for r in refs), "Receipt omits qualification closure")
    return refs
