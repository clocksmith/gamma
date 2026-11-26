var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
var I=0;
while(true){
   var NM=Arr[I].split(" ").map(Number);
   I++;
   var N=NM[0];
   var M=NM[1];
   if(N==0 && M==0)break;
   var n=[];
   for(var i=0;i<N;i++)n[i]=true;
   n[0]=false;
   var tsd=[];
   for(var i=0;i<M;i++){
      var v=Arr[I].split(" ").map(Number);
      I++;
      tsd.push([v[0],v[1]-1,v[2]-1]);
   }
   tsd.sort(function(a,b){return a[0]-b[0];});
   tsd.forEach(function(v){
      var s=v[1];
      var d=v[2];
      if(!n[s])n[d]=false;
   });
   var cnt=0;
   n.forEach(function(v){if(!v)cnt++;});
   console.log(cnt);
}