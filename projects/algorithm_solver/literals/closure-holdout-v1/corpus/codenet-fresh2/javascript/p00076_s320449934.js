var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n").map(Number);
for(var i=0;i<Arr.length;i++){
   if(Arr[i]==-1)break;
   var n=Arr[i]-2;
   var c=Math.sqrt(2);
   var r=45*Math.PI/180;
   while(n!=0){
      r+=Math.atan2(1,c);
      c=Math.sqrt(c*c+1);
      n--;
   }
   var x=c*Math.cos(r);
   var y=c*Math.sin(r);
   console.log(x.toFixed(2));
   console.log(y.toFixed(2));
}