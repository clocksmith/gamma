(function main(){
  let lines = require('fs').readFileSync('/dev/stdin', 'utf8').trim().split("\n");
  let [n, k] = lines.shift().split(' ').map(Number);
  let w = lines.map(Number);

  const canAllStack = (p) => {
    let cnt = 0;
    let sum = 0;
    for (let i = 0; i < k; i++) {
      sum = 0;
      while (sum + w[cnt] <= p) {
        sum += w[cnt++]
        if (cnt === n) return n;
      }
    }
    return cnt;
  };

  let mid, left = 0, right = 1e9;
  while (right - left > 1) {
    mid = Math.floor((right + left) / 2);
    if (canAllStack(mid) >= n) right = mid;
    else left = mid;
  }
  console.log(right);
})();

