const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin
});
rl.on('line', (line) => {
  const k = line.split(' ');
  console.log(k[1] + k[0]);
});
