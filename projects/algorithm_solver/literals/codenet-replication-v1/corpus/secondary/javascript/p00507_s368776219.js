var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
var n=Arr.shift()-0;
Arr.sort(function(a,b){return a-b;});
var ans=[];
for(var i=0;i<5;i++){
   for(var j=i+1;j<5;j++){
      ans.push((Arr[i]+Arr[j])-0);
      ans.push((Arr[j]+Arr[i])-0);
   }
}
ans.sort(function(a,b){return a-b;});
console.log(ans[2]);