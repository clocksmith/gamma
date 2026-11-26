var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
var p="";
var max=0;
for(var i=0;i<Arr.length;i++){
   var arr=Arr[i].split(" ").map(Number);
   if(arr.length==1){
      if(i==0)continue;
      console.log(p+" "+max);
      if(arr[0]=="0")break;
      p="";
      max=0;
   }else{
      var sum=arr[1]+arr[2];
      if(max<=sum){
         max=sum;
         p=arr[0];
       }
   }
}