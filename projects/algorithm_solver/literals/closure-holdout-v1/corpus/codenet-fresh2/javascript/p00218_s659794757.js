var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
for(var i=0;i<Arr.length;i++){
   if(Arr[i]=="0")break;
   var arr=Arr[i].split(" ").map(Number);
   if(arr.length==1)continue;
   var ave=(arr[0]+arr[1]+arr[2])/3;
   var str="C";
   if(arr.indexOf(100)!=-1){str="A";}
   else if((arr[0]+arr[1])/2>=90){str="A";}
   else if(ave>=80){str="A";}
   else if(ave>=70){str="B";}
   else if(ave>=50 && (arr[0]>=80 || arr[1]>=80)){str="B";}
   console.log(str);
}