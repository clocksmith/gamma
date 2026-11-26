(function(input) {
  var p = input.replace(/\n$/, '').split('\n');
  var w = Number(p.shift());
  var n = Number(p.shift());
  var W = [];
  for (var i = 0; i < w; i++) {
    W.push(i);
  }

  for (var i = 0; i < n; i++) {
    var args = p[i].split(',').map(Number);
    var a = args[0];
    var b = args[1];
    var tmp = W[a - 1];
    W[a - 1] = W[b - 1];
    W[b - 1] = tmp;
  }
  console.log(W.map(function(e) { return e + 1; }).join('\n'));
})(require('fs').readFileSync('/dev/stdin', 'utf8'));