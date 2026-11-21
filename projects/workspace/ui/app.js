const $ = selector => document.querySelector(selector);
let projectId = localStorage.getItem('blitzen-project') || localStorage.getItem('fawn-project') || '', pageId = 'main', current = null, pollMs = 1500, timer;
const selectedPages = new Set(['main']);
let artifactsIdentity = '', workflowsIdentity = '', workflowModePinned = false, latestWorkflows = [], workflowBlocked = false;
function notice(text) { $('#notice').textContent = text; $('#notice').hidden = !text; }
async function api(path, options) {
  const response = await fetch(path, { ...options, headers: { 'content-type': 'application/json', ...options?.headers } });
  const value = await response.json(); if (!response.ok) throw Error(value.error || `Request ${response.status}`); return value;
}
async function command(operation, input = {}) {
  const result = await api('/api/command', { method: 'POST', body: JSON.stringify({ operation, projectId, input }) });
  notice(''); return result;
}
function node(tag, text, className) { const element = document.createElement(tag); if (text != null) element.textContent = text; if (className) element.className = className; return element; }
function button(text, action, className) { const element = node('button', text, className); element.type = 'button'; eventListener(element, action); return element; }
function eventListener(element, action) { element.addEventListener('click', () => act(action)); }
async function act(action) { try { await action(); await refresh(); } catch (error) { notice(error.message); } }
function choose(id) { projectId = id; pageId = 'main'; selectedPages.clear(); selectedPages.add('main'); artifactsIdentity = ''; workflowsIdentity = ''; workflowModePinned = false; localStorage.setItem('blitzen-project', id); localStorage.setItem('fawn-project', id); }
function renderWorkflowFields(workflow) {
  const existing = Object.fromEntries([...$('#workflow-fields').querySelectorAll('[data-slot]')].map(input => [input.dataset.slot, input.value]));
  $('#workflow-fields').replaceChildren(...(workflow?.fields ?? []).map(field => {
    const label = node('label', field.label);
    let control;
    if (Array.isArray(field.options) && field.options.length) {
      control = document.createElement('select');
      control.replaceChildren(...field.options.map(option => new Option(option, option)));
    } else {
      control = document.createElement('input');
      control.type = ['email', 'tel', 'url'].includes(field.inputType) ? field.inputType : 'text';
    }
    control.name = field.slot; control.dataset.slot = field.slot;
    if (Object.hasOwn(existing, field.slot)) control.value = existing[field.slot];
    label.append(control); return label;
  }));
}
function syncWorkflowMeta() {
  const active = latestWorkflows.find(item => item.template === $('#workflow-template').value) ?? latestWorkflows[0];
  if (!active) return;
  if (!workflowModePinned && !$('#workflow-form').contains(document.activeElement)) {
    $('#workflow-mode').value = active.hasLearnedGraph ? 'reuse' : 'learn';
  }
  $('#workflow-status').textContent = active.hasLearnedGraph ? `Learned · rev ${active.revision}` : 'Not learned yet';
  $('#workflow-task').textContent = active.task;
  $('#workflow-origin').textContent = `Origin: ${active.origin} · Active tab: ${pageId} · Stops at review without submitting.`;
  const mode = $('#workflow-mode').value;
  $('#run-workflow').disabled = workflowBlocked || (!active.plannerConfigured && (mode !== 'reuse' || !active.hasLearnedGraph));
}
function render(state) {
  pollMs = state.pollMs;
  $('#native-document').hidden = state.nativeDocumentPicker !== true;
  if (state.missingProjectId) { choose(''); notice('That saved investigation is unavailable. Choose one from the list or start a new one.'); }
  const select = $('#projects');
  select.replaceChildren(new Option('New investigation', ''), ...state.projects.map(project => new Option(project.goal.slice(0, 60), project.id)));
  select.value = projectId;
  current = state.selected;
  $('#welcome').hidden = !!current; $('#workspace').hidden = !current;
  if (!current) return;
  const { investigation, workspace } = current;
  $('#goal').textContent = investigation.goal;
  const human = workspace.ownerId === 'human';
  $('#owner').textContent = human ? 'You have control' : 'Agent has control';
  $('#take-over').disabled = human;
  $('#resume-task').hidden = !['stopped', 'needs-attention'].includes(investigation.run?.status);
  $('#run-status').textContent = investigation.run ? `${investigation.run.status.replaceAll('-', ' ')} · ${investigation.run.turns ?? 0} planner requests` : 'Ready when you are';
  const unresolved = workspace.actions.filter(action => action.isUncertain || (action.dispatchStatus === 'dispatched' && !action.outcome));
  const needsReview = Object.values(investigation.artifacts).filter(artifact => artifact.status === 'needs-review');
  const attention = [];
  if (unresolved.length) attention.push(`${unresolved.length} ${unresolved.length === 1 ? 'action' : 'actions'} may have completed. Check their results before submitting again.`);
  if (needsReview.length) attention.push(`${needsReview.length} ${needsReview.length === 1 ? 'conclusion depends' : 'conclusions depend'} on changed evidence or assumptions.`);
  if (investigation.run?.status === 'needs-attention') attention.push(investigation.run.detail);
  $('#attention').hidden = !attention.length; $('#attention').textContent = attention.join(' ');
  // What still holds and what does not, after the last check of saved sources.
  const validity = state.selected?.handoff?.validity;
  const lines = [];
  if (validity?.sourcesCheckedAt) {
    for (const source of validity.changedSources) lines.push(source.missing ? `${source.path} can no longer be read; ${source.affects.length} record(s) rest on it.`
      : `${source.path} changed from line ${source.change.firstChangedLine} (${source.change.removedLines} removed, ${source.change.addedLines} added); ${source.affects.length} record(s) rest on it.`);
    lines.push(`${validity.counts.needsRecheck} record(s) need rechecking, ${validity.counts.stillValid} still hold, ${validity.counts.rejectedHypotheses} rejected explanation(s) kept.`);
    if (validity.uncheckedSources.length) lines.push(`${validity.uncheckedSources.length} saved page(s) were not re-read; use Refresh source on each.`);
    lines.push(`Next: ${validity.nextAction}`);
  }
  $('#validity').hidden = !lines.length; $('#validity').replaceChildren(...lines.map(line => node('p', line)));
  $('#model-status').textContent = state.planner?.model ?? 'Planner not configured';
  // Unconfirmed actions no longer block work: continuing hands them to the agent, which must establish them first.
  if (unresolved.length) $('#resume').checked = true;
  $('#resume').disabled = unresolved.length > 0;
  $('#delegate').disabled = !state.planner || investigation.run?.status === 'running';
  const handoff = state.selected?.handoff;
  $('#handoff-summary').textContent = handoff ? `${handoff.sessions.length} earlier agent session(s) · ${handoff.tried.length} recorded attempt(s) · ${handoff.unresolvedActions.length} unconfirmed action(s) · ${handoff.openQuestions.length} open question(s)` : '';
  for (const id of ['capture', 'select-region', 'open-page']) $(`#${id}`).disabled = !human;
  $('#navigate-form button').disabled = !human;
  const pages = workspace.pages.filter(page => !page.closed);
  if (!pages.some(page => page.pageId === pageId)) pageId = pages[0]?.pageId;
  $('#pages').replaceChildren(...pages.map(page => {
    const row = node('div', null, `page-item${page.pageId === pageId ? ' active' : ''}`);
    const check = document.createElement('input'); check.type = 'checkbox'; check.checked = selectedPages.has(page.pageId);
    check.setAttribute('aria-label', `Share ${page.title || page.url}`); check.onchange = () => check.checked ? selectedPages.add(page.pageId) : selectedPages.delete(page.pageId);
    const label = button(page.title || 'Untitled tab', async () => {
      pageId = page.pageId;
      if (human) await command('focusPage', { pageId });
    }, 'page-select');
    label.append(node('span', page.needsReopen ? `Recovered tab · last at ${page.lastKnownUrl}` : page.url)); row.append(check, label);
    if (page.needsReopen && human) row.append(button('Reopen', () => command('navigate', { pageId: page.pageId, url: page.lastKnownUrl })));
    return row;
  }));
  if (!$('#delegate-form [name=origins]').value && pages.find(page => page.pageId === pageId)?.url.startsWith('http')) {
    $('#delegate-form [name=origins]').value = new URL(pages.find(page => page.pageId === pageId).url).origin;
  }
  latestWorkflows = state.workflows ?? [];
  workflowBlocked = unresolved.length > 0 || investigation.run?.status === 'running';
  $('#workflow-panel').hidden = !latestWorkflows.length;
  if (latestWorkflows.length) {
    const nextWorkflows = JSON.stringify(latestWorkflows.map(({ template, label, fields }) => ({ template, label, fields })));
    if (nextWorkflows !== workflowsIdentity && !$('#workflow-form').contains(document.activeElement)) {
      const chosen = $('#workflow-template').value;
      $('#workflow-template').replaceChildren(...latestWorkflows.map(item => new Option(item.label, item.template)));
      if (latestWorkflows.some(item => item.template === chosen)) $('#workflow-template').value = chosen;
      workflowsIdentity = nextWorkflows;
      renderWorkflowFields(latestWorkflows.find(item => item.template === $('#workflow-template').value) ?? latestWorkflows[0]);
    }
    syncWorkflowMeta();
  }
  $('#grants').replaceChildren(...workspace.grants.filter(grant => grant.ownerId === 'agent').map(grant => {
    const row = node('div', null, 'grant');
    row.append(node('div', `Access: ${grant.targetOrigins.join(', ')} · ${grant.pageIds?.length ?? 0} page(s)`),
      node('div', grant.readRegions === null ? 'Whole selected pages' : `Regions: ${grant.readRegions.join(', ')}`),
      button('Revoke access & take over', () => command('revoke', { grantId: grant.grantId }))); return row;
  }));
  const identity = JSON.stringify(investigation.artifacts);
  if (identity !== artifactsIdentity && !$('#artifacts').contains(document.activeElement)) {
    artifactsIdentity = identity;
    $('#artifacts').replaceChildren(...Object.values(investigation.artifacts).map(artifact => {
      const card = node('article', null, `artifact ${artifact.status}`), top = node('div', null, 'artifact-top');
      top.append(node('span', artifact.kind, 'tag'), node('span', artifact.status === 'needs-review' ? 'Needs review' : `Revision ${artifact.revision}`, 'muted'));
      if (artifact.kind === 'evidence') top.append(button('Refresh source', async () => {
        const input = { artifactId: artifact.id, expectedRevision: artifact.revision };
        if (artifact.source.kind === 'page') await command('capture', { ...input, pageId: artifact.source.pageId });
        else await command('repositoryRead', { ...input, path: artifact.source.path });
      }));
      if (artifact.kind !== 'evidence') top.append(button('Correct', async () => {
        const text = document.createElement('textarea'); text.value = artifact.text;
        const save = button('Save correction', async () => {
          await command('record', { id: artifact.id, kind: artifact.kind, text: text.value, dependsOn: artifact.dependsOn, expectedRevision: artifact.revision });
          artifactsIdentity = ''; text.remove(); save.remove();
        }); card.append(text, save); text.focus();
      }));
      // A competing explanation is settled in the open: supporting or rejecting it needs a reason.
      if (artifact.kind === 'hypothesis') {
        top.append(node('span', artifact.disposition?.state ?? 'open', 'tag'));
        for (const state of ['supported', 'rejected']) if (artifact.disposition?.state !== state) top.append(button(state === 'supported' ? 'Support' : 'Reject', async () => {
          const reason = document.createElement('textarea'); reason.placeholder = `Why is this ${state}? It must rest on at least one saved record.`;
          const save = button(`Save as ${state}`, async () => {
            await command('record', { id: artifact.id, kind: 'hypothesis', text: artifact.text, dependsOn: artifact.dependsOn, expectedRevision: artifact.revision, disposition: { state, reason: reason.value } });
            artifactsIdentity = ''; reason.remove(); save.remove();
          }); card.append(reason, save); reason.focus();
        }));
      }
      card.id = `artifact-${artifact.id}`;
      card.append(top, node('p', artifact.text));
      if (artifact.disposition?.reason) card.append(node('p', `${artifact.disposition.state === 'rejected' ? 'Rejected' : 'Supported'}: ${artifact.disposition.reason}`, 'muted'));
      if (artifact.dependsOn.length) {
        const dependencies = node('div', null, 'dependency-links'); dependencies.append(node('small', 'Depends on'));
        for (const id of artifact.dependsOn) dependencies.append(button(investigation.artifacts[id]?.text.slice(0, 65) || 'Saved record', async () => {
          document.getElementById(`artifact-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 'text-button'));
        card.append(dependencies);
      }
      if (artifact.source) {
        const details = node('details'), summary = node('summary', 'Review saved source'); details.append(summary,
          node('small', artifact.source.url || artifact.source.path), node('small', `SHA-256 ${artifact.source.sha256}`), node('pre', artifact.source.content)); card.append(details);
      }
      return card;
    }));
  }
  if (!$('#dependencies').contains(document.activeElement)) {
    const checked = new Set([...$('#dependencies').querySelectorAll('input:checked')].map(input => input.value));
    $('#dependencies').replaceChildren(...Object.values(investigation.artifacts).map(artifact => {
      const label = node('label', null, 'check'), input = document.createElement('input'); input.type = 'checkbox'; input.name = 'dependsOn';
      input.value = artifact.id; input.checked = checked.has(artifact.id); label.append(input, node('span', `${artifact.kind}: ${artifact.text.slice(0, 90)}`)); return label;
    }));
  }
  $('#artifact-count').textContent = `${Object.keys(investigation.artifacts).length} records`;
  $('#actions').replaceChildren(...workspace.actions.slice().reverse().map(action => {
    const item = node('article', null, `action${action.isUncertain ? ' uncertain' : ''}`);
    const status = action.isUncertain ? 'Unconfirmed: may have completed' : action.outcome ?? action.dispatchStatus;
    item.append(node('strong', `${action.kind} · ${status}`), node('p', `Page: ${action.pageId} · ${action.outcomeBasis ?? 'Not dispatched yet'}`));
    const evidence = node('details'); evidence.append(node('summary', 'Review evidence'), node('pre', JSON.stringify(action, null, 2))); item.append(evidence);
    if (action.isUncertain) {
      item.append(button('Check result', () => command('check', { actionId: action.actionId })));
      const review = node('details'); review.append(node('summary', 'Record a human decision'));
      const note = document.createElement('input'); note.placeholder = 'What did you verify?'; note.setAttribute('aria-label', 'Human verification note');
      for (const [text, decision] of [['I verified it completed', 'effect-present'], ['I verified it did not happen', 'effect-absent']]) {
        review.append(button(text, async () => {
          if (!note.value.trim()) throw Error('Record what you verified before deciding');
          await command('decide', { actionId: action.actionId, decision, note: note.value });
        }));
      }
      review.append(note); item.append(review);
    }
    return item;
  }));
  $('#activity').replaceChildren(...investigation.activity.filter(event => event.type !== 'run-updated' && !['planner-requested', 'planner-result'].includes(event.event)).slice(-8).reverse().map(event => {
    const text = event.event === 'tool-requested' ? `Agent requested ${event.tool}`
      : event.event === 'tool-result' ? 'Tool result recorded'
      : event.event === 'human-control' ? 'You took control'
      : event.event === 'human-note' ? `Note: ${event.text}`
      : event.event === 'delegated' ? event.task
      : event.event === 'personal-workflow-started' ? `Started workflow ${event.template} (${event.mode})`
      : event.event === 'workflow-replay' ? `Replayed ${event.steps} cached step(s) (${event.reason})`
      : event.event === 'personal-workflow-finished' ? `${event.completed ? 'Completed' : 'Stopped'} workflow · ${event.cacheSteps} cached, ${event.modelCalls} model call(s)${event.attempt?.runId ? ` · attempt ${event.attempt.runId.slice(0, 8)}` : ''}`
      : event.event === 'personal-workflow-rejected' ? `Workflow rejected (${event.code})${event.attempt?.runId ? ` · attempt ${event.attempt.runId.slice(0, 8)}` : ''}`
      : event.type === 'artifact-revised' ? `Saved ${event.artifact.kind}`
      : event.event || event.run?.detail || event.type;
    const item = node('li'); item.append(node('time', new Date(event.at).toLocaleString()), node('span', text));
    return item;
  }));
}
async function refresh() {
  const state = await api(`/api/status${projectId ? `?project=${encodeURIComponent(projectId)}` : ''}`); render(state);
}
$('#projects').onchange = () => act(async () => { choose($('#projects').value); });
$('#create-form').onsubmit = event => { event.preventDefault(); act(async () => {
  const data = new FormData(event.target), url = data.get('url');
  const result = await command('create', { goal: data.get('goal'), repositoryRoot: data.get('repositoryRoot') || null }); choose(result.id);
  if (url) await command('navigate', { pageId: 'main', url });
}); };
$('#navigate-form').onsubmit = event => { event.preventDefault(); act(async () => {
  await command('navigate', { pageId, url: new FormData(event.target).get('url') }); event.target.reset();
}); };
$('#workflow-template').onchange = () => {
  workflowModePinned = false;
  renderWorkflowFields(latestWorkflows.find(item => item.template === $('#workflow-template').value) ?? latestWorkflows[0]);
  syncWorkflowMeta();
};
$('#workflow-mode').onchange = () => { workflowModePinned = true; syncWorkflowMeta(); };
$('#workflow-form').onsubmit = event => { event.preventDefault(); act(async () => {
  const inputs = Object.fromEntries([...$('#workflow-fields').querySelectorAll('[data-slot]')].map(input => [input.dataset.slot, input.value]));
  await command('runWorkflow', { template: $('#workflow-template').value, mode: $('#workflow-mode').value, pageId, inputs });
  workflowModePinned = false;
}); };
$('#delegate-form').onsubmit = event => { event.preventDefault(); act(async () => {
  const data = new FormData(event.target), actionKinds = [];
  if (data.has('navigate')) actionKinds.push('navigate');
  if (data.has('interact')) actionKinds.push('click', 'fill', 'select');
  if (data.has('submit')) actionKinds.push('submit'); if (data.has('download')) actionKinds.push('download');
  const files = [...event.target.elements.uploadFiles.files];
  const origins = data.get('origins').split(',').map(value => value.trim()).filter(Boolean);
  if (files.length && !confirm(`Allow this task to disclose ${files.map(file => file.name).join(', ')} to ${origins.join(', ')}? Attachment can send the bytes immediately.`)) return;
  const uploadFiles = await Promise.all(files.map(file => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(Error(`Cannot read ${file.name}`));
    reader.onload = () => resolve({ name: file.name, base64: reader.result.slice(reader.result.indexOf(',') + 1) });
    reader.readAsDataURL(file);
  })));
  if (uploadFiles.length) actionKinds.push('upload');
  await command('delegate', { ...(uploadFiles.length ? { uploadFiles } : {}), pageIds: [...selectedPages], origins: data.get('origins').split(',').map(value => value.trim()).filter(Boolean),
    regions: data.get('regions').trim() ? [data.get('regions').trim()] : null, actionKinds, shareRecords: data.has('shareRecords'), resume: data.has('resume') || $('#resume').checked, task: data.get('task') });
  event.target.elements.uploadFiles.value = '';
}); };
$('#note-form').onsubmit = event => { event.preventDefault(); act(async () => { await command('note', { text: new FormData(event.target).get('text') }); event.target.reset(); }); };
$('#record-form').onsubmit = event => { event.preventDefault(); act(async () => {
  const data = new FormData(event.target); await command('record', { kind: data.get('kind'), text: data.get('text'), dependsOn: data.getAll('dependsOn') }); event.target.reset();
}); };
$('#repository-form').onsubmit = event => { event.preventDefault(); act(() => command('repositoryRead', { path: new FormData(event.target).get('path') })); };
$('#resume-task').onclick = () => {
  const prior = current?.investigation.activity.findLast(event => event.event === 'delegated');
  if (!prior) return;
  $('#delegate-form [name=task]').value = prior.task;
  $('#delegate-form [name=origins]').value = prior.origins.join(', ');
  $('#regions').value = prior.regions?.join(', ') || '';
  for (const [name, kinds] of Object.entries({ navigate: ['navigate'], interact: ['click', 'fill', 'select'], submit: ['submit'], download: ['download'] })) {
    $(`#delegate-form [name=${name}]`).checked = kinds.some(kind => prior.actionKinds.includes(kind));
  }
  $('#delegate-form [name=shareRecords]').checked = true;
  selectedPages.clear();
  for (const id of prior.pageIds) if (current.workspace.pages.some(page => page.pageId === id && !page.closed)) selectedPages.add(id);
  $('#delegate-form').scrollIntoView({ behavior: 'smooth', block: 'center' });
  notice('Review the selected pages, saved records and permissions, then give control to resume. No model call has started.');
};
$('#take-over').onclick = () => act(() => command('takeOver'));
$('#open-page').onclick = () => act(async () => { const page = await command('openPage'); pageId = page.pageId; });
$('#check-sources').onclick = () => act(async () => { await command('checkSources'); artifactsIdentity = ''; });
$('#browse').onclick = () => act(() => command('focusPage', { pageId }));
$('#capture').onclick = () => act(() => command('capture', { pageId }));
$('#select-region').onclick = () => act(async () => { notice('Click the region in your browser page. Escape cancels.'); const result = await command('selectRegion', { pageId }); $('#regions').value = result.selector; });
$('#compact').onclick = () => window.open(location.origin, 'fawn-workspace', 'popup,width=460,height=900');
async function poll() { try { await refresh(); } catch (error) { notice(error.message); } timer = setTimeout(poll, pollMs); }
window.addEventListener('pagehide', () => clearTimeout(timer));
try {
  const token = location.hash.slice(1); history.replaceState(null, '', location.pathname);
  if (token) await api('/api/session', { method: 'POST', body: JSON.stringify({ token }) });
  await poll();
} catch (error) { notice(error.message); }

eventListener($('#native-document'), async () => {
  const result = await api('/api/native-document', { method: 'POST', body: '{}' });
  notice(result.status === 'observed'
    ? `Local document: ${result.byteLength} bytes, SHA-256 ${result.sha256}. Not saved or shared.`
    : 'No current document fingerprint. Select the file again to retry.');
});
