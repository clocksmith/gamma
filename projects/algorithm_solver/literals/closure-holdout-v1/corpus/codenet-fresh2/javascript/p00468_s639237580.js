var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
while(true){
   var n=Arr.shift()-0;
   var m=Arr.shift()-0;
   if(n==0 && m==0)break;
   var ansA={1:true};
   var ansB={1:true};
   var arr=[];
   for(var i=0;i<m;i++){
      var ab=(Arr.shift()).split(" ");
      arr.push(ab);
   }
   for(var i=0;i<m;i++){
      if(arr[i][0]=="1")ansA[arr[i][1]]=true;
   }
   for(var i=0;i<m;i++){
      if(ansA.hasOwnProperty(arr[i][0]) && ansA.hasOwnProperty(arr[i][1])==false)ansB[arr[i][1]]=true;
      if(ansA.hasOwnProperty(arr[i][1]) && ansA.hasOwnProperty(arr[i][0])==false)ansB[arr[i][0]]=true;
   }
   console.log(Object.keys(ansA).length+Object.keys(ansB).length-2);
}