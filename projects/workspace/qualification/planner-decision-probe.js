#!/usr/bin/env node
// Identical synthetic decisions, not end-to-end browser or planner-replacement qualification.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { PLANNER_SYSTEM, PLANNER_TOOLS } from '../src/client/planner.js';

export function judgeDecision(text, task) {
  try {
    const proposal = JSON.parse(text);
    assert.ok(proposal && Object.keys(proposal).every(key => ['tool', 'input'].includes(key)));
    assert.ok(proposal.input && typeof proposal.input === 'object' && !Array.isArray(proposal.input));
    const patterns = [task.expected, ...(task.expected.alternatives ?? [])];
    assert.ok(patterns.some(pattern => {
      try {
        assert.equal(proposal.tool, pattern.tool);
        for (const [key, value] of Object.entries(pattern.input ?? {})) assert.deepEqual(proposal.input[key], value);
        return true;
      } catch { return false; }
    }));
    if (proposal.tool === 'ask_human') assert.ok(typeof proposal.input.reason === 'string' && proposal.input.reason.trim());
    return { correct: true, intervention: false, proposal };
  } catch {
    return { correct: false, intervention: true, reason: 'invalid JSON, wrong tool, or mismatched required input' };
  }
}

async function main() {
  const options = {};
  for (let index = 2; index < process.argv.length; index += 2) {
    const key = process.argv[index];
    if (!['--cloud-model', '--local-model', '--local-url', '--key-file', '--out'].includes(key)
        || !process.argv[index + 1] || options[key]) throw Error('explicit cloud/local models, local URL, key file and new output required');
    options[key] = process.argv[index + 1];
  }
  for (const key of ['--cloud-model', '--local-model', '--local-url', '--key-file', '--out']) assert.ok(options[key], key);
  const local = new URL(options['--local-url']);
  assert.ok(local.protocol === 'http:' && ['127.0.0.1', '[::1]', 'localhost'].includes(local.hostname), 'local planner must be loopback');
  const output = resolve(options['--out']);
  mkdirSync(output, { recursive: false });
  const fixtureBytes = readFileSync(new URL('../test/fixtures/planner-decisions.json', import.meta.url));
  const tasks = JSON.parse(fixtureBytes);
  const key = readFileSync(resolve(options['--key-file']), 'utf8').trim();
  assert.ok(key && !key.includes('\n'), 'one private API key required');
  const hash = value => createHash('sha256').update(value).digest('hex');
  const system = PLANNER_SYSTEM + '\nTool contracts: ' + JSON.stringify(PLANNER_TOOLS)
    + '\nReturn exactly one JSON object {"tool":"name","input":{...}}. No markdown, explanation or reasoning outside JSON.';
  const report = {
    classification: 'diagnostic synthetic planner decisions; no browser effects or replacement verdict',
    sourceSha256: hash(readFileSync(new URL(import.meta.url))), fixtureSha256: hash(fixtureBytes),
    systemSha256: hash(system), observedAt: new Date().toISOString(), outputTokenLimit: 192,
    cloudModel: options['--cloud-model'], localModel: options['--local-model'], localUrl: local.href,
    limitations: ['Six decisions, one sample per provider/case; not complete tasks, a latency percentile, or a general accuracy estimate.',
      'The historical 3.5-6.9s baseline is user-supplied and not used as measured comparison evidence.',
      'Cloud and local use their native HTTP envelopes but identical system, context, permissions and output grammar.',
      'Observed latency is request wall time, including any provider-side preparation; preparation is not separately instrumented and hardware isolation is not established.'], turns: [],
  };
  writeFileSync(join(output, 'cases.json'), fixtureBytes);
  writeFileSync(join(output, 'executed-runner.js'), readFileSync(new URL(import.meta.url)));
  writeFileSync(join(output, 'executed-system.txt'), system);
  async function turn(provider, task) {
    const context = JSON.stringify(task.context);
    const started = performance.now();
    const row = { provider, caseId: task.id, contextSha256: hash(context), status: 'failed' };
    try {
      const response = await fetch(provider === 'cloud' ? 'https://api.anthropic.com/v1/messages' : local, {
        method: 'POST', signal: AbortSignal.timeout(60000),
        headers: { 'content-type': 'application/json', ...(provider === 'cloud' ? {
          'x-api-key': key, 'anthropic-version': '2023-06-01',
        } : {}) },
        body: JSON.stringify(provider === 'cloud' ? {
          model: report.cloudModel, max_tokens: report.outputTokenLimit, system,
          messages: [{ role: 'user', content: context }],
        } : {
          model: report.localModel, max_tokens: report.outputTokenLimit, temperature: 0,
          messages: [{ role: 'system', content: system }, { role: 'user', content: context }],
        }),
      });
      row.httpStatus = response.status;
      if (!response.ok) throw Error(`HTTP ${response.status}`);
      const body = await response.json();
      const text = provider === 'cloud' ? body.content?.filter(block => block.type === 'text').map(block => block.text).join('')
        : body.choices?.[0]?.message?.content;
      row.elapsedMs = performance.now() - started;
      row.actualModel = body.model ?? null;
      row.usage = body.usage ?? null;
      row.finishReason = body.stop_reason ?? body.choices?.[0]?.finish_reason ?? null;
      row.response = text ?? '';
      row.status = 'completed';
      Object.assign(row, judgeDecision(row.response, task));
    } catch (error) {
      row.elapsedMs = performance.now() - started;
      row.error = error.message.replaceAll(key, '[redacted]');
      row.correct = false;
      row.intervention = true;
    }
    report.turns.push(row);
    writeFileSync(join(output, 'result.json'), JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify({ provider, caseId: task.id, correct: row.correct, elapsedMs: row.elapsedMs, error: row.error }));
  }
  for (let index = 0; index < tasks.length; index++) {
    for (const provider of index % 2 ? ['local', 'cloud'] : ['cloud', 'local']) await turn(provider, tasks[index]);
  }
  report.summary = Object.fromEntries(['cloud', 'local'].map(provider => {
    const turns = report.turns.filter(row => row.provider === provider);
    return [provider, { decisions: turns.length, correct: turns.filter(row => row.correct).length,
      interventions: turns.filter(row => row.intervention).length, elapsedMs: turns.map(row => row.elapsedMs) }];
  }));
  writeFileSync(join(output, 'result.json'), JSON.stringify(report, null, 2) + '\n');
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  await main();
}
