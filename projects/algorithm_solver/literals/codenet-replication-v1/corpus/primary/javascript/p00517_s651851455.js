var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
var whn=arr.shift().split(" ").map(Number);
var xy=arr.shift().split(" ").map(Number);
var n=whn[2]-1;
var X=xy[0];
var Y=xy[1];
var sum=0;
while(n--){
   var xy=arr.shift().split(" ").map(Number);
   var x=xy[0];
   var y=xy[1];
   var dx=Math.abs(X-x);
   var dy=Math.abs(Y-y);
   if((x<X && y<Y) || (x>X && y>Y)){
      while(dx>0 && dy>0){
         dx--;
         dy--;
         sum++;
      }
   }
   sum+=dx+dy;
   X=x;
   Y=y;
}
console.log(sum);