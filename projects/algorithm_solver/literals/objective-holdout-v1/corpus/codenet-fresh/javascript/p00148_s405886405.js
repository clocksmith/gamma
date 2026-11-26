var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n").map(Number);
for(var i=0;i<Arr.length;i++){
   var a=Arr[i]%39;
   a=("0"+a).slice(-2);
   if(a=="00")a="39";
   console.log("3C"+a);
}