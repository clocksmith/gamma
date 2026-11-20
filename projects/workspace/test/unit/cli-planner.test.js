import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, writeFileSync, chmodSync, rmSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { createCliPlanner } from '../../src/client/cli-planner.js';
const directory = mkdtempSync(join(tmpdir(), 'fawn-cli-port-'));
const config = JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url)));
const executable = join(directory, 'planner');
try {
  writeFileSync(executable, `#!${process.execPath}\nconst fs=require('node:fs');fs.writeFileSync('arguments.json',JSON.stringify(process.argv.slice(2)));let input='';process.stdin.on('data',s=>input+=s);process.stdin.on('end',()=>{fs.writeFileSync('input.json',input);console.log(JSON.stringify({structured_output:{tool:'finish',input:{summary:'done'}},usage:{input_tokens:3,output_tokens:4},modelUsage:{controlled:{}},total_cost_usd:0.01}));});`);
  chmodSync(executable, 0o700);
  const planner = createCliPlanner({ executable, directory, model: 'selected-model', config });
  const result = await planner.next({ goal: 'Bounded context' }, { signal: new AbortController().signal });
  assert.equal(result.tool, 'finish'); assert.deepEqual(result.usage.models, ['controlled']);
  const args = JSON.parse(readFileSync(join(directory, 'arguments.json')));
  assert.equal(args[args.indexOf('--tools') + 1], '');
  assert.ok(args.includes('--strict-mcp-config')); assert.ok(args.includes('--safe-mode')); assert.ok(args.includes('--restricted'));
  assert.equal(args[args.indexOf('--model') + 1], 'selected-model');
  assert.equal(args[args.indexOf('--max-budget-usd') + 1], String(config.cliMaxBudgetUsd));
  assert.deepEqual(JSON.parse(readFileSync(join(directory, 'input.json'))), { goal: 'Bounded context' });
  const custom = createCliPlanner({ executable, directory, model: 'selected-model', config,
    system: 'Workflow-only system', tools: { finish: 'Stop at review' } });
  await custom.next({}, { signal: new AbortController().signal });
  const customArgs = JSON.parse(readFileSync(join(directory, 'arguments.json')));
  assert.match(customArgs[customArgs.indexOf('--system-prompt') + 1], /^Workflow-only system/);
  assert.deepEqual(JSON.parse(customArgs[customArgs.indexOf('--json-schema') + 1]).properties.tool.enum, ['finish']);
  await assert.rejects(createCliPlanner({ executable, directory, config, tools: { observe: 'Read' } })
    .next({}, { signal: new AbortController().signal }), /valid structured tool/);
  writeFileSync(executable, `#!${process.execPath}\nconsole.log(JSON.stringify({is_error:true,subtype:'error_max_budget_usd',usage:{input_tokens:42},modelUsage:{controlled:{}},total_cost_usd:0.02}));process.exitCode=1;`);
  await assert.rejects(planner.next({ goal: 'budget' }, { signal: new AbortController().signal }), error => {
    assert.match(error.message, /budget reached/); assert.equal(error.usage.costUsd, 0.02); return true;
  });
  writeFileSync(executable, `#!${process.execPath}\nrequire('node:fs').writeFileSync('pid',String(process.pid));setInterval(()=>{},1000);`);
  const controller = new AbortController();
  const pending = planner.next({ goal: 'cancel' }, { signal: controller.signal });
  const assertion = assert.rejects(pending, /human stop/);
  while (!existsSync(join(directory, 'pid'))) await new Promise(resolve => setTimeout(resolve, 5));
  const pid = Number(readFileSync(join(directory, 'pid')));
  controller.abort(Error('human stop')); await assertion;
  assert.throws(() => process.kill(pid, 0), { code: 'ESRCH' });
  console.log('ok: planner-only CLI arguments, explicit model/budget, structured output and cancellation after process settlement');
} finally { rmSync(directory, { recursive: true, force: true }); }
