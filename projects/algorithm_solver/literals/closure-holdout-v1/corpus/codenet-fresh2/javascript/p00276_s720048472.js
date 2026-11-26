var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
var Q=Arr.shift()-0;
for(var i=0;i<Q;i++){
   var arr=(Arr.shift()).split(" ").map(Number);
   var cnt=0;
   while(arr[2]>=1){
      arr[2]--;
      if(arr[0]>=1 && arr[1]>=1){
         cnt++;
         arr[0]--;
         arr[1]--;
      }
   }
   while(arr[1]>=1){
      arr[1]--;
      if(arr[0]>=2){
         cnt++;
         arr[0]-=2;
      }
   }
   while(arr[0]>=3){
      cnt++;
      arr[0]-=3;
   }
   console.log(cnt);
}