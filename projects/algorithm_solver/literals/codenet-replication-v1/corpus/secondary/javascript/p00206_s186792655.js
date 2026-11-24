process.stdin.resume();
process.stdin.setEncoding('utf8');
var input = '';
process.stdin.on('data', function (chunk) {
  input += chunk;
});
process.stdin.on('end', function () {
  var lines = input.split('\n');
  var l = 0;
  while (true) {
    var loan = parseInt(lines[l++]);
    if (loan === 0) {
      break;
    }
    var ans = 'NA';
    for (var i = 0; i < 12; i++) {
      var vs = lines[l++].split(' ');
      loan -= vs[0] - vs[1];
      if (ans === 'NA' && loan <= 0) {
        ans = i + 1;
      }
    }
    console.log(ans);
  }
});