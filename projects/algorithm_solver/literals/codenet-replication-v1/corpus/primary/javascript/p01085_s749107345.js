var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr = input.trim().split("\n");
while (true) {
   var mnn = (arr.shift()).split(" ").map(Number);
   if (mnn[0] == 0) break;
   var Arr = (arr.splice(0, mnn[0])).map(Number);
   var ans = null;
   var max = -Infinity;
   for (var i = mnn[1] - 1; i < mnn[2]; i++) {
      max = Math.max(max, Arr[i] - Arr[i + 1]);
      if (max == Arr[i] - Arr[i + 1]) ans = i;
   }
   console.log(ans + 1);
}