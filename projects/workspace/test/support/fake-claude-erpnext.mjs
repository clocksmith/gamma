#!/usr/bin/env node
// Stand-in for the model CLI in the ERPNext three-arm runner test and dry run. It
// takes the CLI's arguments, starts the MCP server named in --mcp-config, plays a
// fixed script that depends on the tools offered, and prints stream-json events
// with a final result. It makes no model call. The rule it applies is the public
// example's: write only while the quotation behind the order is submitted and is
// for the same total quantity.
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
const rpc = (method, params) => new Promise(done => { const id = nextId++; pending.set(id, done); server.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n'); });
let turn = 0;
const emitUse = (name, input) => console.log(JSON.stringify({ type: 'assistant', message: { id: `msg_${++turn}`, content: [{ type: 'tool_use', id: `tu_${turn}`, name, input }] } }));
const call = async (name, args) => { emitUse(`mcp__app__${name}`, args); return JSON.parse((await rpc('tools/call', { name, arguments: args })).result.content[0].text); };

await rpc('initialize', { protocolVersion: '2025-06-18' });
const tools = (await rpc('tools/list', {})).result.tools.map(t => t.name);
const orders = [...prompt.matchAll(/Purchase Order "([^"]+)", adding the reference "([^"]+)"/g)].map(m => ({ name: m[1], reference: m[2] }));
const familyId = prompt.match(/Family "([^"]+)"/)?.[1] ?? null;
const upgraded = prompt.startsWith('The application has been upgraded');
const keptLines = [...prompt.matchAll(/Family "([^"]+)": Purchase Order "([^"]+)"\. You expected (write|stop)/g)].map(m => ({ familyId: m[1], name: m[2], expect: m[3] }));
let structured = null;

const GUARD = `const doc = (type, name) => '/api/resource/' + encodeURIComponent(type) + '/' + encodeURIComponent(name);
export async function decide({ name, get }) {
  const order = (await get(doc('Purchase Order', name))).body?.data;
  const quotationName = order?.items?.[0]?.supplier_quotation;
  if (!quotationName) return { decision: 'stop', reason: 'no quotation behind the order' };
  const quotation = (await get(doc('Supplier Quotation', quotationName))).body?.data;
  const ok = quotation?.docstatus === 1 && quotation.total_qty === order.total_qty;
  return ok ? { decision: 'write', reason: 'submitted quotation for the same quantity' } : { decision: 'stop', reason: 'quotation does not cover this order' };
}
`;
const PLAN = [{ role: 'order', target: true }, { role: 'quotation', follow: { role: 'order', field: 'items.0.supplier_quotation', doctype: 'Supplier Quotation' } }];
const build = async (quotationQty, submit, orderQty) => {
  const made = await call('erp_request', { as: 'approver', method: 'POST', path: '/api/resource/Supplier%20Quotation', body: { company: 'Stage2 Qual Corp',
    supplier: 'Stage2 Approved Vendor', transaction_date: '2026-02-01', items: [{ item_code: 'STAGE2-UNIT', qty: quotationQty, rate: 100 }] } });
  if (submit) await call('erp_request', { as: 'approver', method: 'POST', path: '/api/method/frappe.client.submit', body: { doc: made.body.data } });
  const order = await call('erp_request', { as: 'author', method: 'POST', path: '/api/resource/Purchase%20Order', body: { company: 'Stage2 Qual Corp',
    supplier: 'Stage2 Approved Vendor', transaction_date: '2026-02-01', schedule_date: '2026-02-15',
    items: [{ item_code: 'STAGE2-UNIT', qty: orderQty, rate: 100, schedule_date: '2026-02-15', supplier_quotation: made.body.data.name }] } });
  return order.body.data.name;
};

if (upgraded && tools.includes('try_guard')) {
  emitUse('Write', { file_path: join(process.cwd(), 'guard.mjs'), content: GUARD });
  writeFileSync(join(process.cwd(), 'guard.mjs'), GUARD);
  await call('try_guard', { familyId, name: orders[0].name });
} else if (upgraded && tools.includes('learn')) {
  await call('set_read_plan', { familyId, reads: PLAN });
  for (const kept of keptLines) await call('add_example', { familyId: kept.familyId, label: kept.expect === 'write' ? 'valid' : 'invalid', name: kept.name });
  await call('learn', { familyId });
} else if (tools.includes('try_guard')) {
  emitUse('Write', { file_path: join(process.cwd(), 'guard.mjs'), content: GUARD });
  writeFileSync(join(process.cwd(), 'guard.mjs'), GUARD);
  await call('erp_request', { as: 'approver', method: 'GET', path: `/api/resource/Purchase%20Order/${encodeURIComponent(orders[0].name)}` });
  await call('try_guard', { familyId, name: orders[0].name });
  const tests = [{ familyId, name: orders[0].name, expect: 'write' }, { familyId, name: await build(7, false, 7), expect: 'stop' }];
  emitUse('Write', { file_path: join(process.cwd(), 'tests.json'), content: JSON.stringify(tests) });
  writeFileSync(join(process.cwd(), 'tests.json'), JSON.stringify(tests));
} else if (tools.includes('learn')) {
  await call('set_read_plan', { familyId, reads: PLAN });
  await call('add_example', { familyId, label: 'valid', name: orders[0].name });
  await call('add_example', { familyId, label: 'valid', name: await build(7, true, 7) });
  await call('add_example', { familyId, label: 'invalid', name: await build(7, false, 7) });
  await call('add_example', { familyId, label: 'invalid', name: await build(4, true, 7) });
  await call('learn', { familyId });
} else {
  const target = orders.at(-1);
  const order = (await call('erp_get', { path: `/api/resource/Purchase%20Order/${encodeURIComponent(target.name)}` })).body?.data;
  const quotationName = order?.items?.[0]?.supplier_quotation;
  const quotation = quotationName ? (await call('erp_get', { path: `/api/resource/Supplier%20Quotation/${encodeURIComponent(quotationName)}` })).body?.data : null;
  const ok = quotation?.docstatus === 1 && quotation.total_qty === order.total_qty;
  structured = { decision: ok ? 'write' : 'stop', reason: ok ? 'submitted quotation for the same quantity' : 'quotation does not cover this order' };
}

server.kill();
console.log(JSON.stringify({ type: 'result', subtype: 'success', is_error: false, num_turns: turn, total_cost_usd: 0.01,
  result: 'DONE', modelUsage: { 'fake-model': {} }, ...(wantsStructured ? { structured_output: structured } : {}) }));
