# Gamma workspace

Gamma owns the workspace package, including browser adapters, authority,
dispatch, journals, recipes and recovery. Stock Chrome is the default. A named,
hash-pinned Fawn build is optional. Fawn and Doe retain browser and WebGPU
ownership. No Gamma research program is required for execution.

Imported from [Fawn source](https://github.com/clocksmith/fawn/tree/9234bc55953c43af7d53c7335d8fe24282e59dc6/browser/workspace)
under the included donor MIT notice. Historical receipts keep their original
bytes and original repository-relative identifiers. They do not qualify this
import or a new browser build. Native desktop support is a follow-up, not an
implemented adapter. Existing state remains opt-in to handoff by preserving the
legacy default path; do not run legacy and Gamma processes against the same
state directory concurrently.

Run `npm ci` and `npm start` in this directory. Run `npm run test:boundary`
for the packaged runtime dependency check. An explicitly supplied workflow
module is trusted operator code, not part of the default runtime closure.

The following upstream description preserves the migration reference.

# Blitzen workspace service

The browser-agnostic shared observation, action, workflow-memory and recovery
service above stock Chrome/Chromium (`@doe/blitzen`, formerly "Fawn Workspace").
Inside [clocksmith/fawn](https://github.com/clocksmith/fawn), three layers have
distinct names and acceptance boundaries:
- **Doe** owns the native WebGPU runtime and WGSL compiler (`Dawn -> Doe`).
- **Fawn** owns the custom Chromium browser build (`Fawn.app`).
- **Blitzen** (`projects/workspace/`) owns durable browser workspaces, workflow
  reuse/repair (`TraceDag`), and investigation handoff above stock Chrome by
  default, with optional hash-pinned `Fawn` browser integration.

The service is JavaScript: an end-to-end C GPU route means selecting Doe's C
compiler/runtime in the Fawn browser, not rewriting Blitzen or Chromium code in C.
[The workspace contract](../../docs/fawn-workspace-contract.md) owns requirements
and acceptance; [status](../../docs/status/fawn-workspace.md) records what is
established (retaining historical `fawn-workspace` filenames and `fawnWorkspace`
strategy keys so frozen evidence hashes stay intact). Its behavior is qualified on the frozen case set for a recorded
commit, browser binary and host. It shows complete-task value over Playwright
agent tooling only on the frozen differentiation suite, and none over competent
scripted automation. Development tests are not the behavioral gates.

## Layout

- `src/service.js`: `WorkspaceService`, the only holder of the workspace browser.
  It owns admission, the trusted dispatcher, handoff, observation recording and
  reconciliation.
- `src/journal.js`, `src/state.js`: the durable hash-chained journal and its
  pure state projection.
- `src/admission.js`, `src/conditions.js`, `src/authority.js`: checks shared by
  admission and dispatch, declarative page conditions, and credentials.
- `src/adapters/`: narrow browser adapters (Playwright, and raw CDP over
  `--remote-debugging-pipe`) plus the shared in-page reader.
- `src/workflows/`: document research, controlled form submission, artifact
  export and engineering incident investigation (`engineering-investigation.js`).
  They contain the task logic and reach the browser only through the
  service API.
- `qualification/`: the behavioral qualification harness and the
  competent-baseline comparison (see [Qualification](#qualification)).
- `test/`: unit tests (fake adapter, real process kills) and a real-Chromium
  qualification subset that also checks the validator rejects tampered evidence.

Tunables and protocol coverage come from
[`config/fawn-workspace-service.json`](./config/fawn-workspace-service.json).

## Explicit file uploads

The human client can select files when delegating a task. It confirms the filenames
and allowed origins before sharing them, then clears the selection for the next
task. A site can read an attached file immediately; no final submit is necessary.
No file or site is implicitly authorized by a learned workflow.

Trusted hosts may instead pass `uploadFiles: [{ name, base64 }]` to an administrator's
`grantAuthorization`, with `upload` in `actionKinds`. The result returns opaque
`fileId`, name, byte length and SHA-256 descriptors. Agent actions use
`kind: 'upload'`, an observed native file-input target (including hidden inputs),
`params: { fileIds: [...] }`, `effect: { external: true, effectKey }`, and explicit
`completion.completedWhen`. No local path is accepted from an agent. A custom
button or drop zone needs an actual file input; an arbitrary non-file element
cannot receive bytes through this action.

The service snapshots selected bytes outside the journal, enforces configured
file/count/staging limits, rechecks authority and the snapshot hash before dispatch,
and uses Playwright or CDP without a native chooser. It first verifies the input's
filename/size list remains attached for the configured settling interval, then
evaluates the caller's completion conditions. `input-files-equal` conditions take
`selector` and `files: [{ name, byteLength }]`; that establishes attachment, not a
server receipt or business acceptance. Sites that clear the input before this
check remain unverified, even if they may already have received bytes. Missing
acknowledgments remain unknown and never authorize automatic retry.

Revocation stops queued actions, but cannot retract already disclosed bytes.
Snapshots remain available to open pages for later submission. After all browsers
close, unused/revoked snapshots are retired; live grants retain snapshots for
restart. Staging exhaustion rejects new selections rather than evicting a file
an open page could still use.

Service config schema 5 adds `uploads` limits and optional upload grants while
retaining protocol 4 and existing journal replay. Config schemas 3 and 4 still
load without uploads. The client request limit includes base64 expansion. Focused
checks: `node projects/workspace/test/unit/uploads.test.js`,
`node projects/workspace/test/browser/uploads.test.js`, and
`node projects/workspace/test/browser/product-uploads.test.js` from the repo root.
These local controlled fixtures do not qualify real-site uploads or model quality.

## Protocol v3

The contract's semantic names map to these concrete rules.

- **Workspace identity.** `workspaceId` (`[a-z0-9-]+`) names one journal entry,
  one persistent Chromium profile under the state directory, and one page.
- **Caller authentication.** Creating a workspace returns an admin credential;
  each `assignOwner` returns an owner credential bound to one owner generation.
  Only SHA-256 hashes are journaled. Owner commands present `ownerId`,
  `ownerGeneration` and the credential; a credential from an earlier generation
  is `stale-owner-generation`, and any other credential is `unauthenticated`.
- **Adapter credentials and mutation coverage.** The service constructs its
  adapter from a factory and never exposes it. Chromium is launched over a
  private pipe, so no debugging port exists for another client. `browser.channel`
  names the build both adapters launch: Playwright's headless shell, Chromium,
  installed Google Chrome, or an explicit hash-bound Fawn build. Automated
  mutations are limited to `actionKinds` in the config: `navigate`, `click`,
  `fill`, `select`, `submit`, `download` and explicitly authorized `upload`. A control that submits a form must
  use `submit`. Anything else is `unsupported-action-kind`. Human browser
  activity remains possible and shows up as page changes.
- **Authorization scope.** An admin grant names one owner, a set of intents,
  action kinds and exact target origins, with an optional expiry. An action needs
  one live grant that covers its `authorizedIntent`, its `kind` and every origin
  it touches: the navigation URL, the current page, the destination of a
  followed link (`click`, `download`) and, for `submit`, the form action. The
  intent check runs before the observation check, so a revoked or expired grant
  is reported as `unauthorized-intent` whatever the page did. Revoking or
  expiring a grant before dispatch ends the action undispatched.
- **Observations and expiry.** Every `observe` records a new version carrying
  the owner generation, a content hash (URL, DOM and control values), element
  target digests, link and form destinations, and an expiry of
  `observation.maxAgeMs`. `observe` may name up to `observation.maxRegions`
  region selectors; the version records a digest of each region's markup and
  control values, or none when the selector does not match exactly one element.
  Targetable elements are links, buttons, inputs, selects, textareas and elements
  with an ARIA widget role (button, link, checkbox, radio, switch, combobox,
  listbox, option, menu items, tab, textbox, searchbox, spinbutton, slider).
  The outline shows a combobox or listbox's current choice and the `checked`,
  `selected` and `expanded` states.
- **Observation scope.** An action's `observationScope` (one of
  `observationScopes`) binds its staleness:
  - `page` (the default): the cited version must be the current one. At
    dispatch the service re-reads the page; any change records a `page-change`
    version and rejects the action as `stale-observation`.
  - `regions`: the cited version may be older, but it must come from the current
    generation, be unexpired and have recorded every scoped region. Later
    versions and the live page at dispatch must keep the cited URL and every
    scoped region digest; otherwise the action is `stale-observation`. Changes
    outside the scoped regions are still recorded as `page-change` versions.
  An empty regions list means the action depends on no page content beyond the
  cited URL; navigation uses it on continuously changing pages. Target identity
  is checked in both scopes.
- **Views for agents.** `observe` also accepts `regionGroups`: every element
  matching a group selector is recorded as its own region under its stable
  selector, for example each product row. `view: 'outline'` returns only:
  - the version, URL and non-atomic boundary
  - each region as a compact outline of its text, with interactive elements
    written as `[handle role "name" = "value"]`
  - `regionGroups`: each requested group selector with the stable selectors of
    the regions it produced, so a scope can cite a group's members

  With `sinceVersion`, a region whose digest matches that version is returned
  as `unchanged`. Digests, element tables and handle tables stay in the journal.
- **Handles.** A handle names an element by a hash of its stable selector, so it
  survives unrelated page changes. An action target `{handle}` resolves through
  the cited observation's handle table to that observation's selector and
  digest, and dispatch checks it like an explicit target.
- **Target identity.** An element target is a `selector` plus the element
  digest (tag, attributes, displayed text and a fingerprint of the full text)
  from the cited observation. At dispatch the selector must match exactly one
  element with the same digest (`target-changed` otherwise).
- **Preconditions.** These are declarative `conditionKinds`, evaluated against
  the live page at dispatch. Text and value conditions need exactly one match
  and read the element's full text; `element-text-excludes` is positive
  evidence of absence only for that one element. A condition that throws or
  times out is unestablished and blocks dispatch.
- **Action records.** Intent is journaled (`action-admitted`) before queueing,
  and `action-dispatch-started` is journaled before the browser effect. Outcomes
  are `completed` or `failed` only with positive evidence: completion or failure
  conditions, a verified value, or a saved artifact hash. Exceptions, timeouts
  and restarts after dispatch began are `unknown`. Queued actions that end at
  dispatch, handoff or restart are `never-dispatched`.
- **Values and choices.** Without caller completion conditions, a `fill` is
  verified with `input-value-equals` and a `select` with `choice-equals`. The
  service polls until the page shows the value, then requires it to stay for
  `dispatch.valueSettleMs`. A value never shown is `unknown` with basis
  `value-unverified`; one shown and then lost, for example to late hydration,
  is `unknown` with basis `value-reverted`. `select` takes an option's value or
  label. It sets a native `<select>` directly. For an ARIA `combobox` it opens
  the popup when collapsed, then clicks the one visible option with that name
  among the elements the combobox names in `aria-controls` or `aria-owns`, or
  anywhere when it names none. For a `listbox` it clicks the option inside it.
  `choice-equals` reads a native select's selected option, a combobox's own
  value or text, or a listbox's single `aria-selected` option. A widget that
  shows its choice elsewhere (some libraries render it beside an empty input)
  stays `value-unverified` unless the caller supplies a completion condition
  that reads where the page shows it.
- **Handoff.** `assignOwner` serializes with admission and dispatch. It
  advances the generation durably and ends queued commands. It returns the
  outstanding records, including in-flight and unknown ones, and the
  non-atomic boundary statement.
- **External effects.** An external effect needs an `effectKey` and completion
  conditions. A new attempt for that effect is refused while an earlier attempt
  is queued, in flight or unknown (`effect-unresolved`), or completed
  (`effect-already-completed`). A permitted retry must name the prior attempt
  in `resubmissionOf`.
- **Reconciliation.** Unknown outcomes stay recorded. Three methods add
  reconciliation records with their basis:
  - `application-state`: conditions on the live page.
  - `external-idempotency`: the original action's external key, never its
    `actionId`. The retry must reuse that key.
  - `human-review`: decided by the workspace admin.
- **Restart.** `WorkspaceService.open` verifies the whole journal chain, ends
  queued actions and marks dispatched actions without outcome `unknown`, and only
  then accepts commands. A corrupt record or a live lock holder fails closed. A
  final record without its terminator was never acted on and is discarded with
  a recorded hash.
- **Migration.** Protocol 2 added observation regions, `observationScope`, link
  destinations and full-text fingerprints. Protocol 3 adds region groups, the
  outline view with deltas, handle targets and empty regions scopes. Earlier
  journals replay unchanged. Their observations carry no handles, and an
  observation without recorded link destinations cannot authorize a `click` or
  `download`. Unknown record types fail closed.

## Qualification

[`config/fawn-workspace-qualification.json`](./config/fawn-workspace-qualification.json)
freezes the behavioral case set: cases, authorization scopes, failure locations,
expected outcomes, the fixture site's hash and the oracles. Each case names a
procedure in `qualification/procedures.js` and runs through every adapter and
every listed workflow.

- `fixture-site.js` serves the corpus, the contact form, export pages and a live
  export page that changes in the background, on a main and a foreign origin.
  Its own request log and receipts are the independent oracle.
- `service-host.js` runs the service in a separate process. The runner kills it
  at declared points, reopens its state and issues concurrent commands so
  handoff can race admission and dispatch.
- `identity.js` binds results to source trees, configs, the commit, running
  browser images and mapped browser code. `process-inspection.js` observes
  processes and listeners through Linux `/proc`, macOS libproc/lsof, or Windows
  CIM/NetTCPIP; adapter assertions do not establish identity.
- `validate.js` admits a full result only if it names committed source and
  matches the frozen case set and fixture. For every run it then:
  - re-verifies and replays the journal and checks ordering invariants
  - compares what callers saw, the journal and the fixture's logs with the
    expectations
  - judges external effects by the application's receipts
  - requires identical behavior across adapters and no debugging endpoint

  It reports coverage of every strategy requirement. Retained evidence paths
  use the producer's OS grammar and must stay inside their evidence directory,
  including after symlink resolution. An optional `case-set.json` snapshot must
  hash to the producer's recorded bytes and contain exactly the current frozen
  rules. This permits cross-platform line endings without changing receipts or
  accepting different expectations. `--require-current-source` additionally
  checks the live service/config/harness identities; offline revalidation does
  not transfer a result to newer source.
- `compare.js` and `baseline/` compare the same workflows against competent
  stock Playwright automation, under the frozen scenarios and criteria in
  `workspaceComparison` of
  [the comparison policy](./config/browser-product-comparison-policy.json).
  The baseline keeps a persistent profile, a durable progress file, an origin
  allowlist, exact locators, the application's idempotency reference and a
  submissions check before resubmitting.
- `differentiate.js`, `differentiation-suites.js` and `agents/` run the frozen
  differentiation suites in `workspaceComparison` and the engineering-investigation suite:
  - `differentiation`: a procurement workbench (`workbench-site.js`)
  - `revalidatedDifferentiation`: a helpdesk (`helpdesk-site.js`) against a
    stronger control that revalidates decisions before mutating and cancels
    pending calls on human takeover
  - `engineeringInvestigation`: an incident queue, runbook and postmortem suite
    (`investigation-site.js`, [`config/fawn-engineering-investigation-suite.json`](./config/fawn-engineering-investigation-suite.json))
    against the same revalidating, takeover-cancelling control

  Each agent has a core (`fawn-agent.js`, `playwright-agent.js`) and a
  per-application profile (`procurement-tools.js`, `helpdesk-tools.js`,
  `investigation-tools.js`).
  - Workload: multipage agent workflows on a live site, judged by that site's
    own records.
  - Agent: one shared policy per application (`agents/procurement-policy.js`,
    `agents/helpdesk-policy.js`, `agents/investigation-policy.js`) decides on
    both sides with the same think time.
  - Treatment: `agents/fawn-agent.js`, a client of this service using outline
    views, region-bound decisions and ownership handoff.
  - Control: `agents/playwright-agent.js` with `agents/playwright-tool-host.js`,
    using Playwright's page-wide incremental agent snapshots and aria-ref actions
    on a browser host that outlives the agent.
- `model-agent/` runs `modelDrivenDifferentiation`: one model drives both sides
  through the frozen prompts and tools (`differentiate.js --suite
  modelDrivenDifferentiation`):
  - `agent-loop.js`: the checkpointed tool loop, restart notice, turn limit and
    input budget
  - `backends.js`: the treatment over this service, and the control over the
    tool host with revalidation and takeover cancellation, refusing with the
    same words
  - `apps.js`: per-application perturbation points and judges; the held-out
    fixtures are in `held-out/`
  - `anthropic-client.js` and `spend-ledger.js`: the frozen request fields,
    bounded retries and a durable ledger that refuses any request whose worst
    case could cross the approved ceiling
  - `model-driven.js`: modes `compatibility`, `smoke`, `full` (once) and
    `offline`. Billed modes need committed source and run in that order.
    `offline` drives any scenario with `scripted-model.js`, a stand-in that
    checks wiring and proves nothing about a model.

## Commands

```bash
cd projects/workspace
npm ci
npm test               # unit tests: journal, service rules, process-kill restart
npm run test:browser   # adds a qualification subset through both adapters
npm run test:browser -- --browser-channel chrome # use installed Chrome for both arms/adapters
npm run qualify        # full case set; writes bench/out/fawn-workspace-qualification/<stamp>
npm run compare        # baseline comparison; writes bench/out/fawn-workspace-comparison/<stamp>
npm run differentiate  # first suite; --suite revalidatedDifferentiation or --suite engineeringInvestigation runs the others
npm run differentiate -- --suite modelDrivenDifferentiation --mode offline --scenarios clinic-clean   # wiring, no API
npm run differentiate -- --suite modelDrivenDifferentiation --mode compatibility   # then smoke, then full
npm run qualify -- --browser-channel chrome   # the case set on installed Google Chrome
xvfb-run -a npm run qualify -- --browser-channel chrome --headless false   # headed, on a virtual display
node qualification/validate.js <resultDir> --require-current-source
```

The browser tests use Playwright's Chromium headless shell by default
(`npx playwright-core install --only-shell chromium`), or installed Chrome with
`--browser-channel chrome`. Channel selection applies equally to both adapters
and both comparison arms; it does not weaken the browser sandbox.
Qualification observes owned processes, actual executable images and TCP listeners
through `/proc` on Linux, `ps`/`lsof` plus libproc through Python3 on macOS,
and CIM/NetTCPIP on Windows. macOS uses kernel executable paths rather than
mutable/truncated process titles.
macOS browser roots, helper images and mapped app frameworks have separate hashes.

### Explicit C browser integration

Service configuration schema 4 adds `browser.channel: "fawn"` and a required
`fawnBuild` containing an absolute browser image path and SHA-256, an explicit
array of dependency file identities, and `runtime.mode: "doe-c"` with the C
library identity. Include the compiler and complete private browser/runtime
closure, including macOS frameworks or Windows `chrome.dll`. Use the actual
browser image, rather than a shell script, `.cmd` or product launcher: qualification
compares it with the executable observed by the OS. Both adapters recheck all
declared files before launch, force Doe with the selected library, keep the
sandbox enabled and reject missing or changed artifacts. Neither adapter retries
with another browser or provider. Explicit `runtime.mode: "dawn"` supplies the
rollback route and accepts no Doe library.

```bash
node qualification/create-browser-profile.js --executable /absolute/browser/image \
  --runtime doe-c --library /absolute/libwebgpu_doe_native.so \
  --dependency /absolute/libdoe_compiler.so --out /absolute/new-c-profile.json
npm run qualify -- --browser-config /absolute/new-c-profile.json
npm run compare -- --browser-config /absolute/new-c-profile.json
npm run differentiate -- --browser-config /absolute/new-c-profile.json
```

Repeat `--dependency FILE` for every additional packaged dependency. The generator
hashes real files and refuses to overwrite its output. Qualification snapshots the
profile and canonical service configuration; only browser fields may differ.
It retains the frozen cases, observes both adapters' actual executable images,
and rejects profile/receipt or executable mismatches. These checks establish
launch identity. Doe ownership still requires the Chromium lane's actual page
compute/presentation, lifecycle and missing-C negative controls; a workspace run
or matching command line alone does not qualify C GPU execution.

Scripted comparisons and both scripted differentiation suites forward the same
profile to treatment and control, retain their frozen headless mode, and require
the selected image to match the OS-observed images. Both also support installed
`--browser-channel` selection. The billed model-driven suite retains its own
frozen browser and rejects these overrides; no profile is silently ignored.

Schema 3 stock-browser configurations remain readable. To select a Fawn build,
start with the schema 4 canonical config; protocol 3 and existing journal records
are unchanged. Existing stock-browser evidence retains its recorded scope.

For the focused dispatcher-to-GPU development control, run:

```bash
node test/browser/gpu-composition.js --browser-config /absolute/new-c-profile.json \
  --out /absolute/new-evidence-directory
```

This uses both real adapters: an authorized click starts ordinary page WGSL
compute and a canvas triangle; the host independently checks all eight numeric
outputs and all 64 RGBA pixels. It requires a reported physical adapter, completed
queue work, canvas frames, cleanup, and a durable completed action after service
restart without resubmission. It binds the fixture, runner, oracle, selected files
and OS-observed browser images; C mode additionally requires the selected runtime
to be observed mapped in the browser process tree. Failed runs stop the sequence
and retain their errors. This is a small composition control, separate from the
frozen behavioral qualification, Chromium missing-C/lifetime gates and application
performance campaigns. It does not establish general browser compatibility or a
product advantage.

The `2026-10-26-behavioral-v3-platform-exits` case freeze retains the same25 cases,
102 runs, fixtures and semantic expectations. Crash evidence now records the
acknowledged controller kill or synchronously received self-kill request separately
from the raw Node close-event tuple. Linux/macOS report signal SIGKILL/code null;
Windows reports that tuple for an acknowledged controller kill, and signal null/code1
for a synchronously received self-kill request. The validator rejects normal exits
and wrong termination codes or missing kill requests rather than fabricating a
POSIX signal on Windows.

## Known limits

- One page per workspace; popups and additional tabs are only counted.
- The outline names a select control by its option text, not its label.
- Page scope treats any DOM change as a page change, so continuously changing
  pages need `regions` scope with the regions an action depends on.
- Chromium answers no page evaluation while a navigation is pending, so
  observations and probes wait for it to commit, bounded by
  `dispatch.actionTimeoutMs`.
- One process holds a journal; the journal is not compacted, and observation
  history is kept for the current owner generation.

## Human workspace client

Normal launches of **Blitzen** use installed Google Chrome (`--browser-channel chrome`) by default,
storing workspace state under `~/.local/state/blitzen`. To run Blitzen against a
hash-pinned **Fawn** browser build instead (`--browser-channel fawn` or
`--browser-config`), create a private profile with
[`qualification/create-browser-profile.js`](qualification/create-browser-profile.js)
selecting the actual executable image (on macOS, `Contents/MacOS/Chromium-real`),
the explicit `doe-c` or `dawn` runtime, and the build's dependency files. When
`fawn` or `--browser-config` is requested, missing or changed artifacts stop
startup with zero fallback to Chrome.

```bash
# Default: launch Blitzen on installed Google Chrome:
npm --prefix projects/workspace start
# Optional explicit planner configuration:
BLITZEN_MODEL=<selected-model> ANTHROPIC_API_KEY=<credential> npm --prefix projects/workspace start
# Explicit hash-pinned Fawn browser build (no fallback):
npm --prefix projects/workspace start -- --browser-config /absolute/browser-profile.json
```

Open the private loopback login link printed by the command. The browser remains
the work surface; **Compact view** opens a companion control window. Create an
investigation, browse its pages, keep source evidence, then delegate only the
selected pages, regions, origins and actions. Saved evidence/notes require separate
disclosure consent. Take over at any time; already dispatched effects may still
complete. **Check result** reads evidence and never repeats an action.

A resumed delegation receives prior attempts, human notes, open questions and
unresolved actions. Handoff pages are bounded; `handoff_read` follows the opaque
cursor in `pagination[collection].nextCursor` to older entries. The total
`unresolvedActionCount` includes actions omitted from the displayed page. A
model's finish proposal cannot complete a run while an action remains unresolved.

Saved evidence stays intact in the journal. Planner context includes a bounded
recent view; `artifact_list` searches and pages through all explicitly shared
records, so long investigations do not eagerly reload every source. `artifact_read` retrieves a bounded range from an explicitly
shared artifact at `expectedRevision`, with source and excerpt hashes. It does
not refresh the source or add filesystem or page permissions. Revising a
conclusion preserves `needs-review` while any supporting premise is unreviewed.

Malformed action proposals can return to the planner only when admission attests
that they were never dispatched and the error is correctable. Rejected proposals
and corrections consume the ordinary request budget. Unknown effects, denied
authority and service failures still stop the run; they are not automatic retries.

State defaults to `~/.local/state/blitzen` (`BLITZEN_STATE_DIR`; legacy
`FAWN_WORKSPACE_STATE_DIR` is also accepted); use `--state-dir` to select another
directory. Admin credentials stay in its private `client-credentials.json`.
`--port`, `--adapter playwright|cdp` and `--headless` select local presentation.
`BLITZEN_BROWSER_CHANNEL` (`chrome` default; `chromium`, `chromium-headless-shell`,
or `fawn`) selects a browser channel, while `BLITZEN_BROWSER_CONFIG` selects a
pinned Fawn profile (`FAWN_BROWSER_*` aliases remain supported). A Fawn profile
and a stock channel cannot be combined. Browser selection does not change
workspace authority. The planner is disabled unless both model and credential are
configured. No model runs on startup.

Protocol 4 adds page identity and opt-in scoped read grants. Earlier journals replay
with main-page compatibility. Restored tabs open blank with an explicit Reopen
control; no page navigation or pending tool is silently repeated. The product
client fences the previous operator and revokes interrupted agent-task grants
during restore. `node projects/workspace/test/browser/product-crash-recovery.test.js`
exercises a real Chromium post followed by SIGKILL before outcome persistence,
then live reconciliation without a duplicate. This development check has been
exercised on macOS Chrome; it is not a cross-platform or performance qualification.
The product client remains unqualified for general task advantage until its own complete-task
comparison passes. Prior frozen-suite results keep their original scope.

With an already authenticated Claude Code installation, select the planner-only
CLI port instead of an API key:

```bash
BLITZEN_PLANNER=claude-cli npm --prefix projects/workspace start
```

The CLI port disables built-in tools, MCP, plugins/project discovery and session
persistence. It runs in a separate empty directory, requests only structured tool
proposals, and records the actual provider-reported model and usage. Its per-turn
budget and cancellation grace are in `fawn-workspace-client.json`. The workspace
service, not the CLI, performs authorized browser actions. No CLI call starts until
a person delegates.

### Investigation comparison

The [controlled shopping comparison](qualification/shopping/README.md) composes
field-trace reuse with fresh product/quote checks and separately authorized order
submission. Its local merchant oracle and scripted control test completion,
repeatability and recovery. It has no live Best Buy adapter or Cerebras comparator.

The optional [trace session prototype](trace-dag.md) records completed
parameterized paths and replays them through the service without planner calls,
stopping at an unknown branch or the pre-submit boundary. It is a programmatic
API, not automatic product-client behavior or a qualified live-site capability.

The [workflow reuse comparison](qualification/workflow-reuse.md) adds explicit
Sonnet-driven learning and safe planner fallback, with a frozen synthetic
application, independent review checks and fresh-planner controls.

The opt-in [personal workflow store](workflow-store.md) persists account-isolated
versions, verified repair suffixes and run records with cross-process publication.
Trusted host task definitions supply account/review verifiers and pre-dispatch
disclosure rules (`--workflow-module PATH` or `openWorkspaceApp({ workflowPersistence, workflowTasks })`).
When host task definitions are installed, the loopback client UI exposes explicit
workflow selection (`learn`, `reuse`, `fresh`) and slot inputs without graph
upload, secret exposure or automatic startup execution.

`node qualification/product-compare.js --out <directory>` compares the product
client with stock Chromium plus the same durable evidence/issue tracker and
planner. The policy fixes source pages, repository code, model, tool contract and
spend ceiling. `--controlled` checks the harness without model calls. The live
probe records provider-reported models/usage, complete-task and preparation wall
time, source hashes, dependency coverage, failures and the independent duplicate
charge reproduction. It is diagnostic: a single pair and mechanical source checks
establish neither semantic answer quality nor a product advantage. Historical
workflow comparisons and frozen promotion criteria remain independently required.

Private cross-client workflow storage and deployment: [shared registry](workflow-registry.md).

### Standalone local document surface

`src/surfaces/local-document.js` is a narrow native observation provider for
an owner-selected, already-open file handle. It reports bounded content
fingerprints of that descriptor only. Reconciliation returns unknown until
a trusted live binding can verify the current document independently of the
open descriptor. Even matching bytes cannot distinguish an atomic safe save. It
does not open arbitrary paths, emit file bytes, write, run commands, request
OS permissions, or resolve a workspace action as successful. The caller owns
the descriptor; detach fences future observations without closing it. The
identity is the selected descriptor's file, not whatever file may later occupy
the same pathname. Metadata stability checks detect the tested concurrent
changes but are not a filesystem transaction.

This is not wired into live workspace dispatch or a macOS picker, and supplies
no browser or native document authority. The local fixture covers observation,
in-place changes, change and detach races, atomic same-name replacement with
matching or different bytes, deletion, and refusal when a live binding, handle
or byte budget is absent.

The standalone selection broker in `src/surfaces/local-document-broker.js`
splits the owner selector from the observation port. The owner UI must call
`owner.select()` from explicit human selection, using a trusted same-process
selector that supplies a read-only handle and release hook. The observation
port can only use an opaque token for the current selection. Cancel keeps the
current selection; replacement, revocation, or close detach it and release
the handle. A late picker result cannot reopen a revoked/closed selection.
Neither port is exposed to workspace recipes or HTTP.

The standalone Swift component in `src/surfaces/macos/SelectedDocument.swift`
can open an explicit AppKit picker and inspect the current selected file.
It retains the selected inode until revocation and uses a fresh, coordinated,
read-only open and revision check for each observation. It does not follow a
move or replacement. After Foundation safe save or any other inode replacement,
the owner must reselect. Neither matching bytes nor a matching Foundation
document identifier proves that a replacement came from the expected writer.
On the tested Mac, a tracked file's identifier also survived an unrelated
same-name replacement; using it alone would have accepted the wrong object.

Run only the generated-file qualification on macOS from this directory:

```sh
build_dir=$(mktemp -d)
xcrun swiftc -warnings-as-errors src/surfaces/macos/SelectedDocument.swift \
  qualification/selected-document-macos.swift -o "$build_dir/check"
"$build_dir/check"
rm -r "$build_dir"
```

The fixture proves in-place observation, fail-closed Foundation safe save,
explicit reselection, and refusal for unrelated identical bytes, deletion,
and symlink substitution. It does not open the picker, prove writer identity,
or integrate with JavaScript/dispatch. A signed App Sandbox host with explicit
user selection and cancellation, denied access and revoke/release still
needs interactive qualification. No retained bookmark or entitlement change
is introduced here.
