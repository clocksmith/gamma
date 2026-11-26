'use strict'

function main(s) {

  s = s.split('\n')[0].split(' ').map(n => Number(n))
  const a = s[0];
  const b = s[1];

  const diff = b - a;
  const bh = [...Array(diff)].map((x, i) => i + 1).reduce((a, b) => a + b);

  const ans = bh - b;
  console.log(ans);

}

main(require("fs").readFileSync("/dev/stdin", "utf8"));
