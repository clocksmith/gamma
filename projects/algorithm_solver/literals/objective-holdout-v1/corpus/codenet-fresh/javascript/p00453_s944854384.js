var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");

while(true){
   var last=[];
   var nm=arr.shift().split(" ").map(Number);
   if(nm.join(" ")=="0 0")break;
   var n=nm[0];
   var m=nm[1];
   var yx=[];
   for(var i=0;i<n;i++){
      var ary=arr.shift().split(" ").map(Number);
      var d=ary.shift();
      var data=[];
      while(d--)data.push([ary.shift(),ary.shift()]);
      yx.push(data);
   }
   var dp=[];
   for(var i=0;i<=n;i++){
      dp[i]=[];
      for(var j=0;j<=1000;j++){
         dp[i][j]=[];
         for(var k=0;k<=m;k++){
            dp[i][j][k]=Infinity;
         }
      }
   }
   yx[0].forEach(function(v){
      var x=v[0];
      dp[0][x][0]=0;
   });
   yx[1].forEach(function(v){
      var x=v[0];
      dp[1][x][1]=0;
   });
   for(var i=1;i<n;i++){
      yx[i].forEach(function(v,index){
         var x=v[0];
         var value=v[1];
         yx[i-1].forEach(function(V,INDEX){
            var X=V[0];
            var VALUE=V[1];
            for(var j=0;j<=m;j++){
               dp[i][x][j]=Math.min(dp[i][x][j],dp[i-1][X][j]+(value+VALUE)*Math.abs(x-X));
            }
         });
      });
      if(i==n-1){
      yx[i].forEach(function(v,index){
         var x=v[0];
         var value=v[1];
         yx[i-1].forEach(function(V,INDEX){
            var X=V[0];
            var VALUE=V[1];
            for(var j=0;j<m;j++){
               dp[i][x][j]=Math.min(dp[i][x][j],dp[i-1][X][j]);
            }
         });
      });
      }
      if(i!=n-1){
      yx[i+1].forEach(function(v,index){
         var x=v[0];
         var value=v[1];
         yx[i-1].forEach(function(V,INDEX){
            var X=V[0];
            var VALUE=V[1];
            for(var j=0;j<m;j++){
               dp[i+1][x][j+1]=Math.min(dp[i+1][x][j+1],dp[i-1][X][j]+(value+VALUE)*Math.abs(x-X));
            }
         });
      });
      }
      
      if(i==n-1 && yx[i].length==0){
         var x=0;
         var value=0;
         yx[i-1].forEach(function(V,INDEX){
            var X=V[0];
            var VALUE=V[1];
            for(var j=0;j<m;j++){
               last.push(dp[i-1][X][j]);
            }
         });
      }
   }
   var min=Infinity;
   yx[n-1].forEach(function(v){
      var x=v[0];
      for(var j=0;j<=m;j++){
         min=Math.min(min,dp[n-1][x][j]);
      }
   });
   if(min==Infinity){
      last.forEach(function(v){
         min=Math.min(min,v);
      });
   }
   console.log(min);
}