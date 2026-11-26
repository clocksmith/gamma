var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
var n=Arr.shift()-0;
for(var i=0;i<n;i++){
   var arr=Arr.shift().split(" ").map(Number);
   (function(x1, y1, x2, y2, x3, y3, x4, y4){
      var k1=(x2-x1!=0)?(y2-y1)/(x2-x1):Infinity;
      var k2=(x4-x3!=0)?(y4-y3)/(x4-x3):Infinity;
      k1=k1.toFixed(6);
      k2=k2.toFixed(6);
      console.log((k1==k2)?"YES":"NO");
   }).apply(null,arr);
}