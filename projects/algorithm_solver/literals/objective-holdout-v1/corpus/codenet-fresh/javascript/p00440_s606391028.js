var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
while(true){
   var nk=Arr.shift().split(" ").map(Number);
   var n=nk[0];
   var k=nk[1];
   if(n==0 && k==0)break;
   var N=[];
   for(var i=0;i<=n+1;i++)N[i]=0;
   for(var i=0;i<k;i++)N[Arr.shift()-0]=1;
   var flag=(N[0]===1)?true:false;
   var str="";
   for(var i=1;i<=n;i++)str+=N[i];
   var arr=str.split("0");
   var maxA=0;
   var maxB=0;
   for(var i=0;i<arr.length-1;i++){
      maxA=Math.max(maxA,arr[i].length+arr[i+1].length);
      maxB=Math.max(maxB,arr[i].length);
   }
   console.log((flag)?maxA+1:maxB);
}