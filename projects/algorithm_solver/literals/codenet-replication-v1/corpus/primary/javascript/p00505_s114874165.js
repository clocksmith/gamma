var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
var ans=[0,0,0,0];
for(var i=0;i<Arr.length;i++){
   var abc=Arr[i].split(" ").map(Number);
   abc.sort(function(a,b){return a-b;});
   var a=abc[0];
   var b=abc[1];
   var c=abc[2];
   if(c<a+b){
      ans[0]++;
      if(c*c==a*a+b*b)ans[1]++;
      if(c*c<a*a+b*b)ans[2]++;
      if(c*c>a*a+b*b)ans[3]++;
   }else{
      break;
   }
}
console.log(ans.join(" "));