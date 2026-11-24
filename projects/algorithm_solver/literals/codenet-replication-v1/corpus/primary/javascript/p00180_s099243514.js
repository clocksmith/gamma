var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
while(true){
   var nm=Arr.shift().split(" ").map(Number);
   var n=nm[0];
   var m=nm[1];
   if(n==0 && m==0)break;
   var N=[];
   for(var i=0;i<n;i++){
      N[i]=[];
      for(var j=0;j<n;j++){
         N[i][j]=Infinity;
         if(i==j)N[i][j]=0;
      }
   }
   var arr=[];
   for(var i=0;i<m;i++){
      var abc=Arr.shift().split(" ").map(Number);
      var a=abc[0];
      var b=abc[1];
      var c=abc[2];
      N[a][b]=c;
      N[b][a]=c;
   }
   var city=[0];
   var cost=0;
   while(true){
      if(city.length==n)break;
      var min=Infinity;
      var select=-1;
      for(var i=0;i<city.length;i++){
         for(var j=0;j<n;j++){
            if(city.indexOf(j)!=-1)continue;
            if(N[city[i]][j]<min){
               select=j;
               min=N[city[i]][j];
            }
         }
      }
      if(select!=-1){
         cost+=min;
         city.push(select);
      }
   }
   console.log(cost);
}