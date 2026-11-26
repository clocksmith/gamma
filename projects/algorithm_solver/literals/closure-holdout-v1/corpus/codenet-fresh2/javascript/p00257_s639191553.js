var input = '';
process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data', function(chunk) {
  input += chunk;
})
process.stdin.on('end', function() {
  main(input.split('\n'));
});

function main (input) {

  var max, n;
  var i;
  while ((max = input.shift() - 0) !== 0) {
    var d = [];
    n = input.shift() - 0;
    d[0] = 0;
    d[n + 1] = 0;
    for (i = 1; i <= n; i++) {
        d[i] = input.shift() - 0;
    }
    console.log(solve(max, n, d) ? 'OK' : 'NG');
  }
}

function makeGraph(n){
  var i, j, g;
  g = [];
  for (i = 0; i < n; i++) {
    g[i] = [];
    for (j = 0; j < n; j++) {
      g[i][j] = i === j ? 0 : Infinity;
    }
  }
  return g;
}

function warshall_floyd(d) {
  var i, j, k,n= d.length;
  for (k = 0; k < n; k++) {
    for (i = 0; i < n; i++) {
      for (j = 0; j < n; j++) {
        d[i][j] = d[i][j] > d[i][k] + d[k][j] ? d[i][k] + d[k][j] : d[i][j];
      }
    }
  }
  return d;
}


function solve(max, n, d) {
    var g = makeGraph(n + 2);
    var i, j;
    var pos;
    for (i = 0; i <= n; i++) {
        for (j = 1; j <=max; j++) {
            pos = i + j + (i + j < n + 1 ? d[i + j] : 0);
            pos = Math.min(Math.max(pos, 0), n + 1);
            if(pos !== i) {
                g[i][pos] = 1;
            }
        }       
    }

    warshall_floyd(g);

    for (i = 0; i <= n; i++) {
      if(g[0][i] < Infinity && g[i][n+1] === Infinity) {
        return false;
      }
    }
    return true;
    
}