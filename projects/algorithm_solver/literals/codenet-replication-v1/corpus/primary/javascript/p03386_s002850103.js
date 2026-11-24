'use strict'

function main(s) {

  s = s.split('\n')[0].split(' ').map(x => Number(x));
  const a = s[0];
  const b = s[1];
  const k = s[2];
  let ans = new Set();

  for (let i = 0; i < k; i++) {
    if ((a + i) <= b || (b - i) >= a) {
      ans.add(a + i);
      ans.add(b - i);
    } else {
      break;
    }
  }

  ans = [...ans].sort((a, b) => a - b).join('\n')
  console.log(ans);
}

main(require("fs").readFileSync("/dev/stdin", "utf8"));
