var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
while(true){
   var nm=(Arr.shift()).split(" ").map(Number);
   if(nm[0]==0 && nm[1]==0)break;
   var n=nm[0];
   var m=nm[1];
   var N=[];
   var M=[];
   for(var i=0;i<n;i++)N.push(Arr.shift()-0);
   for(var i=0;i<m;i++)M.push(Arr.shift()-0);
   var x=0;
   for(var i=0;i<m;i++){
      x+=M[i];
      if(x>=n-1)break;
      x+=N[x];
      if(x>=n-1)break;
   }
   console.log(i+1);
}