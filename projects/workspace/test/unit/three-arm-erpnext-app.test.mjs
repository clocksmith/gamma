import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import {
  ALLOWED_PATH, provisionErpRecipe, validateErpRecipe, validateErpRecipeFile,
} from '../../qualification/workflow-generalization/three-arm-erpnext/erp-app.mjs';

const examples = JSON.parse(readFileSync(
  new URL('../../qualification/workflow-generalization/three-arm-erpnext/example-recipes.json', import.meta.url), 'utf8'));

test('the committed ERPNext examples are well formed', () => {
  assert.deepEqual(validateErpRecipeFile(examples), []);
});

test('only documents and submit or cancel may be called', () => {
  for (const ok of ['/api/resource/Purchase%20Order', '/api/resource/Supplier%20Quotation/PUR-SQTN-2026-00001', '/api/method/frappe.client.submit',
    '/api/method/frappe.client.cancel', '/api/resource/Version?filters=[["docname","=","X"]]']) assert.ok(ALLOWED_PATH.test(ok), ok);
  for (const bad of ['/api/method/frappe.client.delete', '/api/method/frappe.desk.form.save.savedocs', '/api/method/run_doc_method',
    '/app/purchase-order', 'http://example.com/api/resource/X', '/api/resource/../method/x', '/api/v3/work_packages']) assert.ok(!ALLOWED_PATH.test(bad), bad);
});

test('shape problems are reported, and a recipe may not carry its label', () => {
  const recipe = structuredClone(examples.recipes[0]);
  recipe.entryBranch = 'somewhere';
  recipe.setup[1].path = '/api/method/frappe.client.delete';
  recipe.write.reference = 'lower case';
  recipe.target.name = '{missing}';
  const problems = validateErpRecipe(recipe).join('\n');
  for (const expected of [/entryBranch/, /document path or frappe\.client/, /write\.reference/, /target uses \{missing\}/]) assert.match(problems, expected);
  assert.match(validateErpRecipe({ ...examples.recipes[0], valid: true })[0], /must not carry its label/);
  assert.deepEqual(validateErpRecipeFile({ recipes: [examples.recipes[0], examples.recipes[0]] }), ['example-valid: routeId is used twice']);
});

test('provisioning hands the whole saved document to submit and ties the order to the quotation', async () => {
  const calls = [];
  let n = 0;
  const request = async (account, method, path, body) => {
    calls.push({ account, method, path, body });
    if (method === 'GET') return { status: 200, body: { data: { name: 'PUR-ORD-1', docstatus: 0 } } };
    if (path.endsWith('frappe.client.submit')) return { status: 200, body: { message: { ...body.doc, docstatus: 1 } } };
    n += 1;
    return { status: 200, body: { data: { name: path.includes('Quotation') ? `PUR-SQTN-${n}` : `PUR-ORD-${n}`, docstatus: 0, items: body.items } } };
  };
  const route = await provisionErpRecipe(examples.recipes[0], { request, tag: 't' });
  assert.deepEqual([route.doctype, route.name, route.reference, route.entryBranch], ['Purchase Order', 'PUR-ORD-2', 'CONF-1001', 'direct']);
  assert.equal(calls[1].body.doc.name, 'PUR-SQTN-1');
  assert.equal(typeof calls[1].body.doc, 'object');
  assert.equal(calls[2].account, 'author');
  assert.equal(calls[2].body.items[0].supplier_quotation, 'PUR-SQTN-1');
  assert.deepEqual([calls[3].account, calls[3].method], ['approver', 'GET']);
  assert.ok(!('valid' in route));
});

test('a step that fails stops provisioning with the server message, and a submitted target is refused', async () => {
  const refuse = async (account, method, path) => (path.includes('Purchase') ? { status: 417, body: { exception: 'CancelledLinkError: Cannot link cancelled document' } }
    : { status: 200, body: { data: { name: 'PUR-SQTN-1' }, message: {} } });
  await assert.rejects(provisionErpRecipe(examples.recipes[0], { request: refuse }), /returned 417: CancelledLinkError/);
  const submitted = async (account, method) => (method === 'GET' ? { status: 200, body: { data: { docstatus: 1 } } } : { status: 200, body: { data: { name: 'X-1' }, message: {} } });
  await assert.rejects(provisionErpRecipe(examples.recipes[0], { request: submitted }), /must be a draft/);
});
