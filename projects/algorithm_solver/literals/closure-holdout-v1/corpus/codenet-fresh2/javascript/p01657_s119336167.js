var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
var nxm=arr.shift().split(" ").map(Number);
var n=nxm[0];
var x=nxm[1];
var m=nxm[2];
arr=arr.map(function(v){
   v=v.split(" ").map(Number);
   return [v[0]-1,v[1]-1,v[2]];
});
var all=[];
var  loop=function(ary){
   if(ary.length==n)all.push(ary);
   else{
      for(var i=0;i<=x;i++)loop(ary.concat(i))
   }
};
loop([]);
var ans=[-1];
var max=-1;
all.forEach(function(v){
   for(var i=0;i<m;i++){
      var sum=0;
      for(var j=arr[i][0];j<=arr[i][1];j++)sum+=v[j];
      if(sum!=arr[i][2])return;
   }
   sum=v.reduce(function(a,b){return a+b;});
   if(sum>max){ans=v;max=sum;}
});
console.log(ans.join(" "));