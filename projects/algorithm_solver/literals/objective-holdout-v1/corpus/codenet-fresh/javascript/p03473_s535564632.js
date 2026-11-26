process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data', function(a) {
  var n = parseInt(a.toString());
  console.log(48-n);
})