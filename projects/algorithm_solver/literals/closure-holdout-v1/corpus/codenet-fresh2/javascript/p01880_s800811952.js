var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr = input.trim().split("\n");
var a = arr[1].split(" ").map(Number);
var ans = -1;
for (var i = 0; i < a.length; i++) {
   for (var j = i + 1; j < a.length; j++) {
      var v = (a[i] * a[j]) + "";
      var flag = true;
      v.split("").map(Number).reduce(function(a, b) {
         if (a + 1 != b) flag = false;
         return b;
      });
      if (flag) ans = Math.max(ans, v - 0);
   }
}
console.log(ans);