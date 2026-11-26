function Main(input) {
  var inputs = input.split('\n');

  var num = Math.floor(inputs[0]);
  
  var kyoku = [];
  var zikan = [];
  var ans = 0;
  
  for (var i = 1; i <= num; i++) {
    var line = inputs[i].split(' ');
    kyoku.push(line[0]);
    zikan.push(line[1]);
  }
  
  var asleep = inputs[num + 1];
  var sleep = kyoku.indexOf(asleep);
  
  for (var i = sleep + 1; i < kyoku.length; i++) {
    ans += Math.floor(zikan[i]);
  }
  console.log(ans);
}
Main(require('fs').readFileSync('/dev/stdin', 'utf8'));