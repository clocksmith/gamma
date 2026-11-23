// One class letter per source byte, for JavaScript files, using acorn.
//   node lex.cjs <acorn.js> <list file>
// k keyword, i identifier, n number, s string or template text, c comment,
// p punctuation or operator, t indentation, l newline, w other whitespace.
const fs = require('fs');
const acorn = require(process.argv[2]);
const files = fs.readFileSync(process.argv[3], 'utf8').split('\n').filter(Boolean);
const out = {};
for (const file of files) {
  const text = fs.readFileSync(file, 'latin1');
  const marks = Buffer.alloc(text.length, 0x77);
  for (let i = 0; i < text.length; i++) if (text[i] === '\n' || text[i] === '\r') marks[i] = 0x6c;
  const paint = (from, to, c) => marks.fill(c.charCodeAt(0), from, to);
  const comments = [];
  const options = { ecmaVersion: 'latest', sourceType: 'script', allowReturnOutsideFunction: true,
    allowHashBang: true, onComment: comments };
  for (const token of acorn.tokenizer(text, options)) {
    const label = token.type.label;
    if (label === 'name') paint(token.start, token.end, 'i');
    else if (label === 'num' || label === 'bigint') paint(token.start, token.end, 'n');
    else if (label === 'string' || label === 'template' || label === 'regexp') paint(token.start, token.end, 's');
    else if (token.type.keyword) paint(token.start, token.end, 'k');
    else if (label === 'privateId') paint(token.start, token.end, 'i');
    else paint(token.start, token.end, 'p');
  }
  for (const comment of comments) paint(comment.start, comment.end, 'c');
  let lineStart = true;
  for (let i = 0; i < text.length; i++) {
    if (marks[i] === 0x6c) { lineStart = true; continue; }
    if (lineStart && marks[i] === 0x77) marks[i] = 0x74; else lineStart = false;
  }
  out[file] = marks.toString('latin1');
}
process.stdout.write(JSON.stringify(out));
