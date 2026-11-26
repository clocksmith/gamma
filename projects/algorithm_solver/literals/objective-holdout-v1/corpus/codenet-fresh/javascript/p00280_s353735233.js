var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var jy=input.trim().split(" ").map(Number);
var j=jy[0];
var y=jy[1];
var sum=j+y;
var all=[];
var loop=function(ary,j,y,J,Y){
   if(ary.length==sum){
      all.push(ary.join(""));  
   }else{
      if(J==5 && Y==5)return;
      if(J==6 || Y==6)return;      
      if(J<=3 && Y==5)return;      
      if(J==5 && Y<=3)return;  
      if(j>=1)loop(ary.concat("A"),j-1,y,J+1,Y);
      if(y>=1)loop(ary.concat("B"),j,y-1,J,Y+1);
   }
};
loop([],j,y,0,0);
all.sort();
console.log(all.join("\n"));