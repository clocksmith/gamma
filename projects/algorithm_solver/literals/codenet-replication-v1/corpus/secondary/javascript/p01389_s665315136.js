function check(y,x){
   if(y<0 || x<0){return Infinity;}
   else {return yx[y][x];}
}
var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
var hw=(Arr.shift()).split(" ").map(Number);
var h=hw[0];
var w=hw[1];
var yx=[];
for(var i=0;i<h;i++){
   var arr=(Arr.shift()).split("").map(Number);
   yx.push(arr);
}
for(var i=0;i<h;i++){
   for(var j=0;j<w;j++){
      if(i==0 && j==0)continue;
      yx[i][j]=Math.min(check(i-1,j),check(i,j-1))+yx[i][j];
   }
}
console.log(yx[h-1][w-1]);