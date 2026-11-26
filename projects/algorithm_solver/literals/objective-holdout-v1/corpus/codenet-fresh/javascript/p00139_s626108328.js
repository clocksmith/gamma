var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.replace(/\n$/,"")).split("\n");
var n=Arr.shift();
for(var i=0;i<n;i++){
   var str=Arr[i];
   if(/>'(=+)#\1~/.test(str))console.log("A");
   else if(/>\^(Q=)+~~/.test(str))console.log("B");
   else console.log("NA");
}