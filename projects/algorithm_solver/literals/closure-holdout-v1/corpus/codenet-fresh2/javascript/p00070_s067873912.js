var dp=[];
for(var i=0;i<=10;i++){
   dp[i]=[];
   for(var j=0;j<=330;j++){
      dp[i][j]=0;
   }
}

var used=[];
for(var i=0;i<=9;i++)used[i]=false;

function bomb(sum,cnt){
   dp[cnt][sum]++;
   cnt++;
   if(cnt==11)return;
   for(var i=0;i<=9;i++){
      if(used[i])continue;
      used[i]=true;
      bomb(sum+i*cnt,cnt);
      used[i]=false;
   }
}

bomb(0,0);

var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
arr.forEach(function(v){
   var ns=v.split(" ").map(Number);
   var n=ns[0];
   var s=ns[1];
   var ans=(dp[n][s]==undefined)?0:dp[n][s]
   console.log(ans);
});