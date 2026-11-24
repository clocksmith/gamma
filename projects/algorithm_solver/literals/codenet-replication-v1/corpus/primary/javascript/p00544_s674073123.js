var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr = input.trim().replace(/W/g, "0").replace(/B/g, "1").replace(/R/g, "2").split("\n");
var nm = arr.shift().split(" ").map(Number);
var n = nm[0];
var m = nm[1];
var wbr = arr.map(function(v) {
   var color = [m, m, m];
   for (var i = 0; i < m; i++) color[v[i]]--;
   return color;
});
var min = 2500;
for (var i = 0; i < n ; i++) {
   for (var j = 0; j < n ; j++) {
      var flag  = [0,0,0];
      var cost = 0;
      var a = 0;
      while(a<i){
         flag[0] = 1;
         cost += wbr[a][0];
         a++;
      }
      while(a<j){
         flag[1] = 1;
         cost += wbr[a][1];
         a++;
      }
      while(a<n){
         flag[2] = 1;
         cost += wbr[a][2];
         a++;
      }
      if (flag[0] + flag[1] + flag[2] == 3)min = Math.min(cost,min);
   }
}
console.log(min);