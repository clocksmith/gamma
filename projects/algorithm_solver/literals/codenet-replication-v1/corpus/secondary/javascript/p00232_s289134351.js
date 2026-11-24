var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
while(true){
   var xyz=arr.shift().split(" ").map(Number);
   if(xyz.join(" ")=="0 0 0")break;
   var x=xyz[0];
   var y=xyz[1];
   var z=xyz[2];
   var v=arr.shift().split(" ").map(Number);
   var nea=[];
   for(var i=0;i<z;i++){
      var Z=arr.shift().split(" ").map(Number);
      nea[Z[0]]=[Z[1],Z[2]];
   }
   var dp=[];
   for(var i=0;i<=y;i++){
      dp[i]=[];
      for(var j=0;j<=5000;j++){
         dp[i][j]=0;
      }
   }
   dp[0][0]=1;
   for(var i=0;i<y;i++){
      for(var k=0;k<=5000;k++){
         for(var j=0;j<x;j++){
         var after=Math.min(y,i+v[j]);
            if(nea[after]!=undefined){
               var e=nea[after][0];
               var a=nea[after][1];
               if(e==1)dp[Math.min(y,after+a)][k]+=dp[i][k]/x;
               else if(e==2)dp[after][Math.min(5000,k+a)]+=dp[i][k]/x;
               else if(e==3)dp[after][Math.max(0,k-a)]+=dp[i][k]/x;
            }else{
               dp[after][k]+=dp[i][k]/x;
            }
         }
      }
   }
   var sum=0;
   for(var i=0;i<=5000;i++)sum+=i*dp[y][i];
   console.log(Math.floor(sum));
}