function bigAdd(x,y){
   var a=(x+"").split("").reverse().map(Number);
   var b=(y+"").split("").reverse().map(Number);
   var c=[];
   var max=Math.max(a.length,b.length);
   for(var i=0;i<max+1;i++)c[i]=0;
   for(var i=0;i<max;i++){
      var sum=0;
      if(a.length>i)sum+=a[i];
      if(b.length>i)sum+=b[i];
      c[i]+=sum;
   }
   for(var i=0;i<max;i++){
      if(c[i]>=10){
         c[i]-=10;
         c[i+1]++;
      }
   }
   if(c[c.length-1]==0)c.pop();
   var str=c.reverse().join("");
   return str;
}
var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
var n=Arr.shift()-0;
var arr=(Arr.shift()).split(" ").map(Number);
var last=arr.pop();
n--;
var dp=[];
for(var i=0;i<n;i++){
   dp[i]=[];
   for(var j=0;j<=20;j++){
      dp[i][j]=0;
   }
}
dp[0][arr[0]]=1;
for(var i=1;i<n;i++){
   var v=arr[i];
   for(var j=0;j<=20;j++){
      if(dp[i-1][j]!==0){
         if(j+v<=20)dp[i][j+v]=bigAdd(dp[i][j+v],dp[i-1][j]);
         if(j-v>=0)dp[i][j-v]=bigAdd(dp[i][j-v],dp[i-1][j]);
      }
   }
}
console.log(dp[n-1][last]);