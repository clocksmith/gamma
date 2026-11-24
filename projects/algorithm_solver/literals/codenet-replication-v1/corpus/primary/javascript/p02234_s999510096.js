function range(begin, end) {
  return Array.from(Array(end - begin), (e, i) => begin + i);
}

(function main() {
  const lines = require('fs').readFileSync('/dev/stdin', 'utf8').trim().split('\n');
  const n = Number(lines.shift ());
  const p = lines.map(l => l.split(' ')[0]).concat([lines[n-1].split(' ')[1]]).map(Number);

  const m = Array.from(Array(n + 1), () => (Array(n + 1)));
  for (let i = 1; i < n + 1; i++) m[i][i] = 0;

  let i = 0, d = 1;
  for (d = 1; d <= n - 1; d++) {
    for (i = 1; i <= n - d; i++) {
      m[i][i+d] = range(i, i + d).map(
        k => m[i][k] + m[k + 1][i + d] + p[i - 1] * p[k] * p[i + d]
      ).sort((a, b) => a - b)[0];
    }
  }
  console.log(m[1][n]);
})();

