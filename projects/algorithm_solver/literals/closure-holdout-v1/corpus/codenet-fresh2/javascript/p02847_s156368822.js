process.stdin.resume();
process.stdin.setEncoding('utf8');

var lines = []
var reader = require('readline').createInterface({
  input: process.stdin,
  output: process.stdout
});

reader.on('line', (line) => {
  lines.push(line);
});

reader.on('close', () => {
  var N = lines[0];
  var days = [ 'SUN','MON','TUE','WED','THU','FRI','SAT' ];
  var idx = days.indexOf(N);
  var result = 7 - idx;
  console.log(result);
});