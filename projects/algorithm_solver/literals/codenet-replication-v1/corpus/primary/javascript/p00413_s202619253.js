var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
var [x,y,w,h]=arr.shift().split(" ").map(Number);
var [xx,yy,ww,hh]=arr.shift().split(" ").map(Number);
var yx=[];
for(var i=0;i<=2000;i++){
   yx[i]=[];
   for(var j=0;j<=2000;j++)yx[i][j]=0;
}
for(var i=y;i<y+h;i++)for(var j=x;j<x+w;j++)yx[i][j]=1;
for(var i=yy;i<yy+hh;i++)for(var j=xx;j<xx+ww;j++){
   if(yx[i][j]==1)yx[i][j]=0;
   else yx[i][j]=1;
}
var cnt=0;
for(var i=0;i<=2000;i++)for(var j=0;j<=2000;j++){
   if(yx[i][j]==1)cnt++;
}
console.log(cnt);
