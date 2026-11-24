var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
var nm=(Arr.shift()).split(" ").map(Number);
var n=[];
for(var i=0;i<nm[0];i++){
   n.push([i+1,Arr.shift()-0,0]);
}
for(var i=0;i<nm[1];i++){
   var v=Arr.shift()-0;
   for(var j=0;j<nm[0];j++){
      if(n[j][1]<=v){
         n[j][2]++;
         break;
      }
   }
}
n.sort(function(a,b){
   a=a[2];
   b=b[2];
   return b-a;
});
console.log(n[0][0]);