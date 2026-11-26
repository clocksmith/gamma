(function(input) {
  var p = input.replace(/\n$/, '').split('\n');
  var a, b;
  var hit, blow;
  while ((a = p.shift()) && (b = p.shift())) {
    a = a.split(' ').map(Number);
    b = b.split(' ').map(Number);
    hit = blow = 0;
    for (var i = 0; i < b.length; i++) {
      if (a[i] === b[i]) {
        hit++;
      } else if (a.indexOf(b[i]) >= 0) {
        blow++;
      }
    }
    console.log('%d %d', hit, blow);
  }
})(require('fs').readFileSync('/dev/stdin', 'utf8'));