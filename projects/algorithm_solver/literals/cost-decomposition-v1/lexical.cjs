// Byte-aligned lexical attribution only; never execute supplied programs.
const fs = require('node:fs');
const acorn = require('/usr/share/nodejs/acorn');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const output = {};
for (const [id, text] of Object.entries(input)) {
  if ([...text].some(c => c.codePointAt(0) > 127)) throw Error('ASCII contract');
  const tokens = [], comments = [];
  acorn.parse(text, {ecmaVersion: 'latest', onToken: tokens, onComment: comments});
  const labels = Array(text.length).fill('syntax.layout');
  for (const t of tokens) {
    const k = t.type.label;
    let category;
    if (k === 'eof') continue;
    if (k === 'name' || k === 'privateId') category = 'identifier';
    else if (['num','string','regexp','true','false','null','template','invalidTemplate'].includes(k)) category = 'literal';
    else if (t.type.keyword) category = 'syntax.keyword';
    else if (t.type.binop != null || t.type.isAssign || t.type.prefix || t.type.postfix || ['=>','...','?'].includes(k)) category = 'syntax.operator';
    else category = 'syntax.delimiter';
    labels.fill(category, t.start, t.end);
  }
  for (const c of comments) labels.fill('syntax.comment', c.start, c.end);
  output[id] = labels;
}
process.stdout.write(JSON.stringify(output));
