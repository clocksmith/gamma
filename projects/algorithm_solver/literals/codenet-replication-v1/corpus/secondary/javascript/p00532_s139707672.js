var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=input.trim().split("\n");
var n=Arr.shift()-0;
var ans=[];
for(var i=0;i<n;i++)ans[i]=0;
var m=Arr.shift()-0;
var t=Arr.shift().split(" ").map(function(v){return ~~v-1;});
for(var I=0;I<m;I++){
   var arr=Arr[I].split(" ").map(function(v){return ~~v-1;});
   var target=t[I];
   var bad=0;
   arr.forEach(function(v,i){
      (v==target)?ans[i]++:bad++;
   });
   ans[target]+=bad;
}
console.log(ans.join("\n"));