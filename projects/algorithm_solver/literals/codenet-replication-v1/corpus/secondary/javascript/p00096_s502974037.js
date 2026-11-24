var ab=[];
for(var i=0;i<=2000;i++)ab[i]=0;
for(var i=0;i<=1000;i++){
   for(var j=0;j<=1000;j++){
      ab[i+j]++;
   }
}
var arr=[];
for(var i=0;i<=4000;i++)arr[i]=0;
for(var i=0;i<ab.length;i++){
   for(var j=0;j<ab.length;j++){
      arr[i+j]+=ab[i]*ab[j];
   }
}
var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
while(Arr.length!=0){
   console.log(arr[Arr.shift()-0]);
}