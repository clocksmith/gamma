var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
while(true){
   var cnmsd=arr.shift().split(" ").map(Number);
   if(cnmsd.join(" ")=="0 0 0 0 0")break;
   var c=cnmsd[0];
   var n=cnmsd[1];
   var m=cnmsd[2];
   var s=cnmsd[3];
   var d=cnmsd[4];
   var ary=[];
   for(var i=0;i<m;i++)ary.push(arr.shift().split(" ").map(Number));
   var dp=[];
   for(var i=0;i<=n;i++){
      dp[i]=[];
      for(var j=0;j<=c;j++){
         dp[i][j]=Infinity;
      }
   }
   dp[s][0]=0;
   var bomb=[s];
   var obj={};
   while(true){
      if(bomb.length==0)break;
      var S=bomb.shift();
      if(obj.hasOwnProperty(S))continue;
      obj[S]=true;
      ary.forEach(function(v){
         var a=v[0];
         var b=v[1];
         var f=v[2];
         if(a==S){
            dp[a].forEach(function(v,i){
               dp[b][i]=Math.min(dp[b][i],v+f);
               if(i<c)dp[b][i+1]=Math.min(dp[b][i+1],v+f/2);
            });
            bomb.push(b);
         }else if(b==S){
            dp[b].forEach(function(v,i){
               dp[a][i]=Math.min(dp[a][i],v+f);
               if(i<c)dp[a][i+1]=Math.min(dp[a][i+1],v+f/2);
            });
            bomb.push(a);
         }
      });
   }
   var ans=Infinity;
   dp[d].forEach(function(v){
      ans=Math.min(ans,v);
   });
   console.log(ans);
}