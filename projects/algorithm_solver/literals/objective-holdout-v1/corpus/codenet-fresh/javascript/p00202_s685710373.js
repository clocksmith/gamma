function main() {
  var
  n, m,
  i = 0, j, ans, dp, dp_, x, k, line, xs;
  for(;;) {
    line = input[i++].split(' ').map(parseFloat);
    n = line[0]; m = line[1];
    if (n === 0 && m === 0) break;
    
    xs = [];
    for (j = 0; j < n; j++) {
      xs.push(parseInt(input[i++], 10));
    }
    
    dp = {};
    ans = 0;
    dp[0] = true;
    for (j = 0; j < n; j++) {
      for (k = xs[j]; k <= m; k++) {
        if (dp[k - xs[j]]) {
          dp[k] = true;
          if (ps[k]) ans = Math.max(ans, k);
        }
      }
    }

    console.log(ans || 'NA');
  }
}

function prims(n) {
  var
  i, j,
  prims = [false, false];
  for (i = 2; i <= n; i++) prims[i] = true;
  for (i = 2; i <= n; i++) if (prims[i]) {
    for (j = i + i; j <= n; j += i) prims[j] = false;
  }
  return prims;
}

var
ps = prims(1000000);

var
input = '';

process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data', function(chunk) {
  input += chunk;
});
process.stdin.on('end', function() {
  input = input.split('\n');
  main();
});