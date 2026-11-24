function count(x,y){
   if(xy[x][y]==-1)return;
   var dx=[0,-1];
   var dy=[-1,0];
   var sum=0;
   for(var i=0;i<2;i++){
      var xx=x+dx[i];
      var yy=y+dy[i];
      if(xx<0 || yy<0 || xy[xx][yy]==-1)continue;
      sum+=xy[xx][yy];
   }
   xy[x][y]=sum;
}
var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
while(true){
   var ab=Arr.shift();
   if(ab=="0 0")break;
   ab=ab.split(" ").map(Number);
   var a=ab[0];
   var b=ab[1];
   var n=Arr.shift()-0;
   var xy=[];
   for(var i=0;i<a;i++){
      xy[i]=[];
      for(var j=0;j<b;j++){
         xy[i][j]=0;
      }
   }
   xy[0][0]=1;
   for(var i=0;i<n;i++){
      var ab=(Arr.shift()).split(" ").map(Number);
      xy[ab[0]-1][ab[1]-1]=-1;
   }
   for(var i=0;i<a;i++){
      for(var j=0;j<b;j++){
         if(i==0 && j==0)continue;
         count(i,j);
      }
   }
   console.log(xy[a-1][b-1]);
}