function warshall(){
   for(var k=0;k<nm[1];k++){
      for(var i=0;i<nm[1];i++){
         for(var j=0;j<nm[1];j++){
            C[i][j]=Math.min(C[i][j], C[i][k]+C[k][j]);
            T[i][j]=Math.min(T[i][j], T[i][k]+T[k][j]);
         }
      }
   }
}
var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
while(true){
   var nm=(Arr.shift()).split(" ").map(Number);
   if(nm[0]==0 && nm[1]==0)break;
   var C=[];
   var T=[];
   for(var i=0;i<nm[1];i++){
      C[i]=[];
      T[i]=[];
      for(var j=0;j<nm[1];j++){
         C[i][j]=(i===j)?0:Infinity;
         T[i][j]=(i===j)?0:Infinity;
      }
   }
   for(var i=0;i<nm[0];i++){
      var A=(Arr.shift()).split(" ").map(Number);
      C[A[0]-1][A[1]-1]=C[A[1]-1][A[0]-1]=Math.min(A[2],C[A[0]-1][A[1]-1]);
      T[A[0]-1][A[1]-1]=T[A[1]-1][A[0]-1]=Math.min(A[3],T[A[0]-1][A[1]-1]);
   }
   warshall();
   var k=Arr.shift()-0;
   for(var i=0;i<k;i++){
      var B=(Arr.shift()).split(" ").map(Number);
      if(B[2]==0)console.log(C[B[0]-1][B[1]-1]);
      if(B[2]==1)console.log(T[B[0]-1][B[1]-1]);
   }
}