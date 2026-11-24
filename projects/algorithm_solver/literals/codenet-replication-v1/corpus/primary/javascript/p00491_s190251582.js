var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
var nk=arr.shift().split(" ").map(Number);
var n=nk[0];
var k=nk[1];
var obj={};
for(var i=0;i<k;i++){
   var ab=arr.shift().split(" ").map(Number);
   obj[ab[0]]=ab[1]-1;
}
var dp=[];
for(var i=0;i<=n;i++){
   dp[i]=[];
   for(var j=0;j<3;j++){
      dp[i][j]=[];
      for(var k=0;k<3;k++){
         dp[i][j][k]=0;
      }
   }
}
dp[1][0][1]=1;
dp[1][1][1]=1;
dp[1][2][1]=1;

for(var i=1;i<=n;i++){
   dp[i][0][2]+=dp[i-1][0][1]%10000;
   dp[i][1][2]+=dp[i-1][1][1]%10000;
   dp[i][2][2]+=dp[i-1][2][1]%10000;

   dp[i][1][1]+=dp[i-1][0][1]%10000;
   dp[i][1][1]+=dp[i-1][0][2]%10000;
   dp[i][2][1]+=dp[i-1][0][1]%10000;
   dp[i][2][1]+=dp[i-1][0][2]%10000;

   dp[i][0][1]+=dp[i-1][1][1]%10000;
   dp[i][0][1]+=dp[i-1][1][2]%10000;
   dp[i][2][1]+=dp[i-1][1][1]%10000;
   dp[i][2][1]+=dp[i-1][1][2]%10000;

   dp[i][0][1]+=dp[i-1][2][1]%10000;
   dp[i][0][1]+=dp[i-1][2][2]%10000;
   dp[i][1][1]+=dp[i-1][2][1]%10000;
   dp[i][1][1]+=dp[i-1][2][2]%10000;
   if(obj.hasOwnProperty(i)){
      for(var v=0;v<3;v++){
         if(obj[i]!=v){
            dp[i][v][1]=0;
            dp[i][v][2]=0;
         }
      }
   }
}
var sum=0;
for(var i=0;i<3;i++){
   for(var j=1;j<=2;j++){
      sum+=dp[n][i][j];
   }
}
console.log(sum%10000);