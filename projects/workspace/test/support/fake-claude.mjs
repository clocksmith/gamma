#!/usr/bin/env node
// Stand-in for the model CLI in the three-arm runner test. It takes the same
// arguments, starts the MCP server named in --mcp-config, plays a fixed script
// that depends on which tools that server offers, and prints stream-json events
// with a final result, as the real CLI does. It makes no model call.
import { spawn } from 'node:child_process';
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';

const argv = process.argv.slice(2);
const option = name => argv[argv.indexOf(name) + 1];
const config = JSON.parse(option('--mcp-config')).mcpServers.app;
const wantsStructured = argv.includes('--json-schema');
let prompt = '';
for await (const chunk of process.stdin) prompt += chunk;

const server = spawn(config.command, config.args, { env: { ...process.env, ...config.env }, stdio: ['pipe', 'pipe', 'inherit'] });
const pending = new Map();
let buffer = '';
server.stdout.on('data', chunk => {
  buffer += chunk;
  for (let cut; (cut = buffer.indexOf('\n')) !== -1; buffer = buffer.slice(cut + 1)) {
    const message = JSON.parse(buffer.slice(0, cut));
    pending.get(message.id)?.(message);
    pending.delete(message.id);
  }
});
let nextId = 1;
const rpc = (method, params) => new Promise(done => {
  const id = nextId++;
  pending.set(id, done);
  server.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n');
});
let turn = 0;
const emitUse = (name, input) => console.log(JSON.stringify({ type: 'assistant',
  message: { id: `msg_${++turn}`, content: [{ type: 'tool_use', id: `tu_${turn}`, name, input }] } }));
const call = async (name, args) => {
  emitUse(`mcp__app__${name}`, args);
  const reply = await rpc('tools/call', { name, arguments: args });
  return JSON.parse(reply.result.content[0].text);
};

await rpc('initialize', { protocolVersion: '2025-06-18' });
const tools = (await rpc('tools/list', {})).result.tools.map(t => t.name);
const numbers = [...prompt.matchAll(/number (\d+) in project "([^"]+)"[^\n]*?(\d+) hours/g)]
  .map(m => ({ workPackageId: Number(m[1]), project: m[2], workHours: Number(m[3]) }));
const familyId = prompt.match(/Family "([^"]+)"/)?.[1] ?? null;
let structured = null;

const GUARD = `const hours = d => { const m = String(d ?? '').match(/^P(?:(\\d+)D)?(?:T(?:(\\d+)H)?)?$/); return m ? Number(m[1] ?? 0) * 24 + Number(m[2] ?? 0) : null; };
export async function decide({ workPackageId, workHours, get }) {
  const record = await get('/api/v3/work_packages/' + workPackageId);
  const parent = record.body?._links?.parent?.href;
  if (!parent) return { decision: 'stop', reason: 'no approval above it' };
  const approval = await get(parent);
  const approved = String(approval.body?._links?.status?.href ?? '').endsWith('/16');
  const same = hours(approval.body?.estimatedTime) === workHours;
  return approved && same ? { decision: 'write', reason: 'approved for these hours' } : { decision: 'stop', reason: 'approval does not cover this' };
}
`;
const build = async (hours, status) => {
  const approval = await call('app_request', { as: 'approver', method: 'POST', path: '/api/v3/projects/stage2-qual-proj/work_packages',
    body: { subject: 'approval', estimatedTime: `PT${hours}H` } });
  await call('app_request', { as: 'approver', method: 'PATCH', path: `/api/v3/work_packages/${approval.body.id}`,
    body: { lockVersion: 0, _links: { status: { href: `/api/v3/statuses/${status}` } } } });
  const order = await call('app_request', { as: 'author', method: 'POST', path: '/api/v3/projects/stage2-qual-proj/work_packages',
    body: { subject: 'order', estimatedTime: 'PT8H', _links: { parent: { href: `/api/v3/work_packages/${approval.body.id}` } } } });
  return order.body.id;
};

const upgraded = prompt.startsWith('The application has been upgraded');
const keptLines = [...prompt.matchAll(/Family "([^"]+)": number (\d+) in project "([^"]+)", saving Work as (\d+) hours\. You expected (write|stop)/g)]
  .map(m => ({ familyId: m[1], workPackageId: Number(m[2]), project: m[3], workHours: Number(m[4]), expect: m[5] }));

if (upgraded && tools.includes('try_guard')) {
  // The statuses were renumbered: read the approved one from the disclosed example instead of assuming 16.
  const repaired = GUARD.replace("String(approval.body?._links?.status?.href ?? '').endsWith('/16')",
    "String(approval.body?._links?.status?.href ?? '').endsWith('/26')");
  emitUse('Edit', { file_path: join(process.cwd(), 'guard.mjs'), old_string: "'/16'", new_string: "'/26'" });
  writeFileSync(join(process.cwd(), 'guard.mjs'), repaired);
  await call('try_guard', { familyId, ...numbers[0] });
} else if (upgraded && tools.includes('learn')) {
  await call('set_read_plan', { familyId, reads: [{ role: 'record', path: '/api/v3/work_packages/{target}' }, { role: 'approval', follow: { role: 'record', link: 'parent' } }] });
  for (const kept of keptLines) await call('add_example', { familyId: kept.familyId, label: kept.expect === 'write' ? 'valid' : 'invalid',
    project: kept.project, workPackageId: kept.workPackageId, workHours: kept.workHours });
  await call('learn', { familyId });
} else if (tools.includes('try_guard')) {
  const file = join(process.cwd(), 'guard.mjs');
  emitUse('Write', { file_path: file, content: GUARD });
  writeFileSync(file, GUARD);
  await call('app_request', { as: 'approver', method: 'GET', path: `/api/v3/work_packages/${numbers[0].workPackageId}` });
  await call('try_guard', { familyId, ...numbers[0] });
  const tests = [{ familyId, ...numbers[0], expect: 'write' },
    { familyId, project: 'stage2-qual-proj', workPackageId: await build(40, 17), workHours: 40, expect: 'stop' }];
  emitUse('Write', { file_path: join(process.cwd(), 'tests.json'), content: JSON.stringify(tests) });
  writeFileSync(join(process.cwd(), 'tests.json'), JSON.stringify(tests));
} else if (tools.includes('learn')) {
  await call('set_read_plan', { familyId, reads: [{ role: 'record', path: '/api/v3/work_packages/{target}' }, { role: 'approval', follow: { role: 'record', link: 'parent' } }] });
  await call('add_example', { familyId, label: 'valid', ...numbers[0] });
  await call('add_example', { familyId, label: 'valid', project: 'stage2-qual-proj', workPackageId: await build(40, 16), workHours: 40 });
  await call('add_example', { familyId, label: 'invalid', project: 'stage2-qual-proj', workPackageId: await build(40, 17), workHours: 40 });
  await call('add_example', { familyId, label: 'invalid', project: 'stage2-qual-proj', workPackageId: await build(16, 16), workHours: 40 });
  await call('learn', { familyId });
} else {
  const target = numbers.at(-1);
  const record = await call('app_get', { path: `/api/v3/work_packages/${target.workPackageId}` });
  const parent = record.body?._links?.parent?.href;
  const approval = parent ? await call('app_get', { path: parent }) : null;
  const asHours = d => { const m = String(d ?? '').match(/^P(?:(\d+)D)?(?:T(?:(\d+)H)?)?$/); return m ? Number(m[1] ?? 0) * 24 + Number(m[2] ?? 0) : null; };
  const ok = String(approval?.body?._links?.status?.href ?? '').endsWith('/16') && asHours(approval?.body?.estimatedTime) === target.workHours;
  structured = { decision: ok ? 'write' : 'stop', reason: ok ? 'approved for these hours' : 'approval does not cover this' };
}
if (process.env.FAKE_CLAUDE_MISBEHAVE === '1') emitUse('Bash', { command: 'cat /etc/passwd' });

server.kill();
console.log(JSON.stringify({ type: 'result', subtype: 'success', is_error: false, num_turns: turn, total_cost_usd: 0.01,
  result: 'DONE', modelUsage: { 'fake-model': {} }, ...(wantsStructured ? { structured_output: structured } : {}) }));
