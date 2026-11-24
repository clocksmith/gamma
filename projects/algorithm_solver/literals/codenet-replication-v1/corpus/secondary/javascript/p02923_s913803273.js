'use strict';
function main(input) {
  const args = input.split('\n'),
        N = parseInt(args[0]),
        H = args[1].split(' ');
  let cnt = 0;
  let tmp = 0;
  for (let i = 0; i < N-1; ++i) {
    if (parseInt(H[i]) >= parseInt(H[i+1])) {
      ++tmp;
      if (i === N-2 && tmp > cnt) {
        cnt = tmp;
      }
    } else {
      if (tmp > cnt) {
        cnt = tmp;
      }
      tmp = 0;
    }
  }
  console.log(cnt);
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'));