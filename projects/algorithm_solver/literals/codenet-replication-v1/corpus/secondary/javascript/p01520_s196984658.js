var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
var NTE=Arr.shift().split(" ").map(Number);
var N=NTE[0];
var T=NTE[1];
var E=NTE[2];
var x=Arr.shift().split(" ").map(Number);
var ans=-1;
for(var i=0;i<N;i++){
   if(ans!=-1)break;
   var time;
   var j=1;
   while(true){
      time=x[i]*j;
      if(T+E<time)break;
      if(T-E<=time && time<=T+E){ans=i+1;break;}
      j++;
   }
}
console.log(ans);