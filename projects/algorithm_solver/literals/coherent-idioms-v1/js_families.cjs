// Grammar-owned complete literal spans; source-as-data only, using existing Acorn stack.
'use strict';
const fs = require('node:fs');
const acorn = require('internal/deps/acorn/acorn/dist/acorn');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const result = {};
for (const [id, source] of Object.entries(input)) {
  const tokens = [], comments = [];
  const tree = acorn.parse(source, {ecmaVersion: 2022, onToken: tokens, onComment: comments});
  const byte = n => Buffer.byteLength(source.slice(0, n));
  const spans = [];
  const add = (a, b, kind) => { if (a < b) spans.push([byte(a), byte(b), kind]); };
  function walk(n) {
    if (!n || typeof n !== 'object') return;
    if (['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'].includes(n.type) && n.body.type === 'BlockStatement')
      add(n.start, n.body.start + 1, 'function_opening');
    if (['IfStatement', 'SwitchStatement', 'WithStatement', 'CatchClause'].includes(n.type)) {
      const body = n.consequent || n.body;
      if (body && typeof body.start === 'number') add(n.start, body.start + (body.type === 'BlockStatement' ? 1 : 0), 'condition_opening');
    }
    const kinds = {ReturnStatement:'return_statement', VariableDeclaration:'declaration',
      ExpressionStatement:'expression_statement', ThrowStatement:'throw_statement',
      BreakStatement:'control_statement', ContinueStatement:'control_statement',
      CallExpression:'call_expression', NewExpression:'construction_expression',
      BinaryExpression:'binary_expression', LogicalExpression:'binary_expression',
      ConditionalExpression:'conditional_expression', ArrayExpression:'collection_expression',
      ObjectExpression:'collection_expression', MemberExpression:'member_expression'};
    if (kinds[n.type]) add(n.start, n.end, kinds[n.type]);
    // Constructor fragments are AST-role boundaries, never token windows.
    const prefix = (child, kind) => { if (child) add(n.start, child.start, kind); };
    const suffix = (child, kind) => { if (child) add(child.end, n.end, kind); };
    if (['Identifier','Literal','ThisExpression'].includes(n.type)) {
      const whole = tokens.find(t => t.start === n.start && t.end === n.end);
      if (whole && [...source.slice(n.start,n.end)].length >= 2) add(n.start,n.end,'lexical_operand');
    }
    if (['ReturnStatement','ThrowStatement','AwaitExpression','YieldExpression','UnaryExpression'].includes(n.type))
      prefix(n.argument,'keyword_or_unary_opening');
    if (n.type === 'VariableDeclaration' && n.declarations.length)
      prefix(n.declarations[0],'declaration_opening');
    if (['AssignmentExpression','BinaryExpression','LogicalExpression','VariableDeclarator'].includes(n.type)) {
      const left=n.left || n.id, right=n.right || n.init;
      if (left && right) {
        add(n.start,right.start,'operation_left_phrase');
        add(left.end,n.end,'operation_right_phrase');
        add(left.end,right.start,'operation_operator');
      }
    }
    if (n.type === 'UpdateExpression') add(n.start,n.end,'update_phrase');
    if (['CallExpression','NewExpression'].includes(n.type)) {
      const open=tokens.find(t => t.start>=n.callee.end && t.end<=n.end && t.type.label==='(');
      if (open) add(n.start,open.end,'call_opening');
      if (n.arguments.length) suffix(n.arguments[n.arguments.length-1],'call_closing');
    }
    if (n.type === 'MemberExpression') {
      if (n.computed) add(n.start,n.property.start,'index_opening');
      else add(n.object.end,n.end,'member_operation');
      if (n.computed) add(n.property.end,n.end,'index_closing');
    }
    if (['IfStatement','WhileStatement','SwitchStatement'].includes(n.type)) {
      const test=n.test || n.discriminant, body=n.consequent || n.body;
      prefix(test,'condition_constructor');
      if (test && body && typeof body.start==='number') add(test.end,body.start+(body.type==='BlockStatement'?1:0),'condition_closing');
    }
    if (['ForStatement','ForOfStatement','ForInStatement'].includes(n.type)) {
      const first=n.init || n.left || n.test || n.update;
      if (first) prefix(first,'loop_constructor');
      const last=n.update || n.right || n.test || n.init;
      if (last) add(last.end,n.body.start+(n.body.type==='BlockStatement'?1:0),'loop_header_closing');
    }
    if (['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression'].includes(n.type) && n.body.type==='BlockStatement') {
      const open=tokens.find(t => t.start>=n.start && t.end<=n.body.start && t.type.label==='(');
      if (open) add(n.start,open.end,'function_constructor');
      if (n.params.length) add(n.params[0].start,n.body.start+1,'parameter_bindings');
      if (n.params.length) add(n.params[n.params.length-1].end,n.body.start+1,'function_header_closing');
    }
    // An else opening includes its keyword and brace, rather than an arbitrary
    // token window. It remains exact text, not a parameterized control macro.
    if (n.type === 'IfStatement' && n.alternate && n.alternate.type === 'BlockStatement') {
      const keyword = tokens.find(t => t.start >= n.consequent.end && t.end <= n.alternate.start && t.type.keyword === 'else');
      if (keyword) add(keyword.start, n.alternate.start + 1, 'condition_opening');
    }
    for (const [key, value] of Object.entries(n)) {
      if (['start','end','type'].includes(key)) continue;
      if (Array.isArray(value)) value.forEach(walk);
      else if (value && typeof value === 'object') walk(value);
    }
  }
  walk(tree); result[id] = {spans, comments: comments.map(c => [byte(c.start), byte(c.end)])};
}
process.stdout.write(JSON.stringify(result));
