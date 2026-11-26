var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split(" ");
var num=0;
for(var i=0;i<Arr.length;i++){
   var str=Arr[i];
   str=str.replace(/\d+/g,function(s){
      num+=(s-0);
      return s;
   });
}
console.log(num);