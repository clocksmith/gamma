var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var str=input.trim();
var arr=str.split("");
var kupc=[0,0,0,0];
arr.forEach(function(v){
   if(v=="K")kupc[0]++;
   if(v=="U")kupc[1]++;
   if(v=="P")kupc[2]++;
   if(v=="C")kupc[3]++;
});
console.log(Math.min.apply(null,kupc));