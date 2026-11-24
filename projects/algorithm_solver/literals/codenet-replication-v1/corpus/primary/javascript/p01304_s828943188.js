var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
var n=Arr.shift()-0;
for(var I=0;I<n;I++){
   var xy=Arr.shift().split(" ").map(Number);
   var X=xy[0];
   var Y=xy[1];
   var p=Arr.shift()-0;
   var xx=[];
   var yy=[];
   for(var i=0;i<p;i++){
      var v=Arr.shift().split(" ").map(Number);
      if(v[0]==v[2])yy.push([Math.max(v[1]+1,v[3]+1),v[0]+1].join(","));
      else xx.push([v[1]+1,Math.max(v[0]+1,v[2]+1)].join(","));
   }
   var YX=[];
   for(var i=0;i<=Y+1;i++){
      YX[i]=[];
      for(var j=0;j<=X+1;j++){
         YX[i][j]=0;
      }
   }
   YX[1][1]=1;
   for(var y=1;y<=Y+1;y++){
      for(var x=1;x<=X+1;x++){
         if(y==1 && x==1)continue;
         var str=[y,x].join(",");
         if(yy.indexOf(str)!=-1 && xx.indexOf(str)!=-1)YX[y][x]=0;
         else if(yy.indexOf(str)!=-1)YX[y][x]=YX[y][x-1];
         else if(xx.indexOf(str)!=-1)YX[y][x]=YX[y-1][x];
         else YX[y][x]=YX[y-1][x]+YX[y][x-1];
      }
   }
   console.log((YX[Y+1][X+1]==0)?"Miserable Hokusai!":YX[Y+1][X+1]);
}