var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr =input.trim().split("\n");
var ndx=arr.shift().split(" ").map(Number);
var n=ndx[0];
var d=ndx[1];
var x=ndx[2];
var day=[];
for(var i=0;i<d;i++)day.push(arr.shift().split(" ").map(Number));
var item=[];
for(var i=0;i<d-1;i++){
   item[i]=[""];
   for(var j=0;j<n;j++){
      item[i].push([day[i][j],day[i+1][j]-day[i][j]]);
   }
}
function DP(k){
   var dp=[];
   for(var i=0;i<=n;i++){
      dp[i]=[];
      for(var j=0;j<=x;j++){
         dp[i][j]=0;
      }
   }
   for(var i=1;i<=n;i++){
      for(var j=1;j<=x;j++){
         var c=item[k][i][0];
         var w=(item[k][i][1]<0)?0:item[k][i][1];
         if(c<=j)dp[i][j]=Math.max(dp[i-1][j],w+dp[i-1][j-c],w+dp[i][j-c]);
         else dp[i][j]=dp[i-1][j];
      }
   }
   return x+dp[n][x];
}
for(var i=0;i<d-1;i++){
   x=DP(i);
}
console.log(x);