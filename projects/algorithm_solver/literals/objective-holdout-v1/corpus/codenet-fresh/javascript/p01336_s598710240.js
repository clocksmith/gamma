var input = require('fs').readFileSync('/dev/stdin', 'utf8');

var arr=input.trim().split("\n");
while(arr.length!=0){
var nm=arr.shift().split(" ").map(Number);
var n=nm[0];
var m=nm[1];
var item1=[""];
var item2=[""];
var item3=[""];
for(var i=0;i<n;i++){
arr.shift();
var CVDL=arr.shift().split(" ").map(Number);
item1.push([CVDL[0],CVDL[1]]);
item2.push([CVDL[0],CVDL[2]]);
item3.push([CVDL[0],CVDL[3]]);
}

var ans=[];

var dp=[];
for(var i=0;i<=n;i++){
dp[i]=[];
for(var j=0;j<=m;j++){
dp[i][j]=0;
}
}

for(var i=1;i<=n;i++){
for(var j=1;j<=m;j++){
   var c=item1[i][0];
   var w=item1[i][1];
   if(c<=j)dp[i][j]=Math.max(dp[i-1][j],w+dp[i-1][j-c],w+dp[i][j-c]);
   else dp[i][j]=dp[i-1][j];
}
}

ans.push(dp[n][m]);

var dp=[];
for(var i=0;i<=n;i++){
dp[i]=[];
for(var j=0;j<=m;j++){
dp[i][j]=0;
}
}

for(var i=1;i<=n;i++){
for(var j=1;j<=m;j++){
   var c=item2[i][0];
   var w=item2[i][1];
   if(c<=j)dp[i][j]=Math.max(dp[i-1][j],w+dp[i-1][j-c],w+dp[i][j-c]);
   else dp[i][j]=dp[i-1][j];
}
}

ans.push(dp[n][m]);

var dp=[];
for(var i=0;i<=n;i++){
dp[i]=[];
for(var j=0;j<=m;j++){
dp[i][j]=0;
}
}

for(var i=1;i<=n;i++){
for(var j=1;j<=m;j++){
   var c=item3[i][0];
   var w=item3[i][1];
   if(c<=j)dp[i][j]=Math.max(dp[i-1][j],w+dp[i-1][j-c],w+dp[i][j-c]);
   else dp[i][j]=dp[i-1][j];
}
}

ans.push(dp[n][m]);

console.log(Math.max(ans[0],ans[1],ans[2]));


}