var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
var I=0;
while(true){
   var nS=Arr[I].split(" ").map(Number);
   I++;
   var n=nS[0];
   var S=nS[1];
   if(n==0 && S==0)break;
   var arr=[];
   for(var i=0;i<n;i++){
      var r=Arr[I]-0;
      I++;
      arr.push(r);
   }
   arr.sort(function(a,b){return a-b;});
   var cnt=0;
   for(var i=0;i<n;i++){
      for(var j=i+1;j<n;j++){
         if(arr[i]+arr[j]>S){cnt+=n-j;break;}
      }
   }
   console.log(cnt);
}