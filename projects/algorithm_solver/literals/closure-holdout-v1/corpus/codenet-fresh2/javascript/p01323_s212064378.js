function bomb(y,x,color){
   var dy=[-1,0,0,1];
   var dx=[0,-1,1,0];
   for(var i=0;i<4;i++){
      var yy=y+dy[i];
      var xx=x+dx[i];
      if(yy<0 || xx<0 || yy>=12 || xx>=6)continue;
      if(yx[yy][xx]==color) {
         CNT++;
         if(CNT==4)p.push([yy,xx]);
         yx[yy][xx]=color+0;
         bomb(yy,xx,color);
      }
   }
}
function BOMB(y,x,color){
   var dy=[-1,0,0,1];
   var dx=[0,-1,1,0];
   for(var i=0;i<4;i++){
      var yy=y+dy[i];
      var xx=x+dx[i];
      if(yy<0 || xx<0 || yy>=12 || xx>=6)continue;
      if(yx[yy][xx]==color){
         yx[yy][xx]=".";
         BOMB(yy,xx,color);
      }else if(yx[yy][xx]=="O"){
         yx[yy][xx]=".";
      }
   }
}
function up(y,x){
   var yy=y;
   while(y>0){
      y--;
      if(yx[y][x]!="."){
         yx[yy][x]=yx[y][x];
         yx[y][x]=".";
         break;
      }
   }
}
var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
var n=Arr.shift()-0;
for(var I=0;I<n;I++){
   var yx=[];
   for(var i=0;i<12;i++){
      var arr=(Arr.shift()).split("");
      yx.push(arr);
   }
   var result=0;  
   while(true){
        var p=[];
        var CNT;
         for(var i=0;i<12;i++){
               for(var j=0;j<6;j++){
                  if(yx[i][j]=="R"){yx[i][j]="R"+0;CNT=1;bomb(i,j,"R");}
                  if(yx[i][j]=="G"){yx[i][j]="G"+0;CNT=1;bomb(i,j,"G");}
                  if(yx[i][j]=="B"){yx[i][j]="B"+0;CNT=1;bomb(i,j,"B");}
                  if(yx[i][j]=="Y"){yx[i][j]="Y"+0;CNT=1;bomb(i,j,"Y");}
                  if(yx[i][j]=="P"){yx[i][j]="P"+0;CNT=1;bomb(i,j,"P");}
               }
         }
         for(var i=0;i<12;i++){
            for(var j=0;j<6;j++){
               yx[i][j]=yx[i][j].slice(0,1);
            }
         }
         if(p.length==0)break;
         result++; 
         p.forEach(function(v){
            var i=v[0];
            var j=v[1];
            var color=yx[i][j];
            if(color!=".")BOMB(i,j,color);
         });
         for(var i=11;i>0;i--){
            for(var j=0;j<6;j++){
               if(yx[i][j]==".")up(i,j);
            }
         }
   }
   console.log(result);
}