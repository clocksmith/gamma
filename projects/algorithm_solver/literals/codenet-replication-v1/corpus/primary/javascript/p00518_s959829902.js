var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
var n=arr.shift();
var ary=arr.shift().split("");
var dp=[];
for(var i=0;i<=n;i++){
   dp[i]={};
   dp[i]["--I"]=0;
   dp[i]["-O-"]=0;
   dp[i]["J--"]=0;
   dp[i]["-OI"]=0;
   dp[i]["J-I"]=0;
   dp[i]["JO-"]=0;
   dp[i]["JOI"]=0;
}
dp[0]["J--"]=1;
var key=["--I","-O-","J--","-OI","J-I","JO-","JOI"];
for(var i=1;i<=n;i++){
   var joi=ary[i-1];
   for(var j=0;j<key.length;j++){
      var B=key[j];
      for(var k=0;k<key.length;k++){
          var A=key[k];
          if(A.indexOf(joi)==-1)continue;
          var flag=false;
          for(var p=0;p<3;p++){
             if(A[p]!="-" && A[p]==B[p])flag=true;
          }
          if(flag==false)continue;
          dp[i][A]+=dp[i-1][B]%10007;
      }
   }
}
var sum=0;
for(var k in dp[n]){
   sum+=dp[n][k];
}
console.log(sum%10007);