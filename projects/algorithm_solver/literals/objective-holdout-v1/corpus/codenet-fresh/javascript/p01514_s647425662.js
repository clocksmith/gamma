var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
while(true){
   var tpr=(Arr.shift()).split(" ").map(Number);
   if(tpr[0]==0 && tpr[1]==0 &&  tpr[2]==0)break;
   var G=[];
   var Tp=[];
   for(var i=0;i<tpr[0];i++){
      G[i]=[i,0,0];
      Tp[i]=[];
      for(var j=0;j<tpr[1];j++){
         Tp[i][j]=0;
      }
   }
   for(var i=0;i<tpr[2];i++){
      var arr=(Arr.shift()).split(" ");
      var t=(arr[0]-0)-1;
      var p=(arr[1]-0)-1;
      var time=arr[2]-0;
      if(arr[3]=="WRONG")Tp[t][p]++;
      if(arr[3]=="CORRECT"){
         G[t][1]++;
         G[t][2]+=(Tp[t][p]*1200)+time;
      }
   }
   G.sort(function(a,b){
      a=((50-a[0])*0.01)+(a[1]*1000000)+(610800-a[2]);
      b=((50-b[0])*0.01)+(b[1]*1000000)+(610800-b[2]);
      return b-a;
   });
   G.forEach(function(v){
      console.log((v[0]+1)+" "+v[1]+" "+v[2]);
   });
}