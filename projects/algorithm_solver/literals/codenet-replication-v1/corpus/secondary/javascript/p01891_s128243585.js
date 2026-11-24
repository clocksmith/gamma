var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr = input.trim().split("\n");
var nmab = arr[0].split(" ").map(Number);
var d = arr[1].split(" ").map(Number);
var m = nmab[1];
var a = nmab[2];
var b = nmab[3];
var haiki = [];
 
for (var i = 0; i < d.length; i++) {
   if (d[i] >= a) haiki.push(d[i]);
   else break;
}
 
if (d.length - haiki.length < m) {
   haiki.reverse();
   var cnt = 0;
   for (var i = 0; i < haiki.length; i++) {
      if (haiki[i] <= b) cnt++;
      else break;
   }
   console.log(haiki.length - cnt);
} else {
   console.log(haiki.length);
}