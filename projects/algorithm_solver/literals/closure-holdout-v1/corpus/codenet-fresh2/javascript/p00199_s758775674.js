function AA(){
   for(var i=1;i<arr.length-1;i++){
      if(arr[i]==0){arr[i]="A";return;}
   }
}
function BB(){
   for(var i=arr.length-2;i>=1;i--){
      if(arr[i-1]!="A" && arr[i]==0 && arr[i+1]!="A"){arr[i]="B";return;}
   }
   for(var i=1;i<arr.length-1;i++){
      if(arr[i]==0){arr[i]="B";return;}
   }
}
function CC(){
   for(var i=1;i<arr.length-1;i++){
      if(arr[i]!=0 && arr[i+1]==0){arr[i+1]="C";return;}
      if(arr[i]!=0 && arr[i-1]==0){arr[i-1]="C";return;}
   }
   if(n%2==1)arr[(n-1)/2+1]="C";
   if(n%2!=1)arr[n/2+1]="C";
}
function DD(){
   var max=[0,0];
   for(var i=1;i<arr.length-1;i++){
      if(arr[i]!=0)continue;
      var jA=i;
      var jB=i;
      var cnt=0;
      while(true){
         if(arr[jA]!="X")jA--;
         if(arr[jB]!="X")jB++;
         if(arr[jA]=="X" && arr[jB]=="X")break;
         if(arr[jA]!="X" && arr[jA]!=0)break;
         if(arr[jB]!="X" && arr[jB]!=0)break;
         cnt++;
         if(max[1]<cnt)max=[i,cnt];
      }
   }
   if(max[1]!=0){arr[max[0]]="D";return;}
   for(var i=1;i<arr.length-1;i++){
      if(arr[i]==0){arr[i]="D";return;}
   }
}
var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=input.trim().split("\n");
while(true){
   var nm=Arr.shift().split(" ").map(Number);
   var n=nm[0];
   var m=nm[1];
   if(n==0 && m==0)break;
   var arr=[];
   for(var i=0;i<n;i++)arr.push(0);
   arr.unshift("X");
   arr.push("X");
   for(var i=0;i<m;i++){
      var v=Arr.shift();
      if(v=="A")AA();
      if(v=="B")BB();
      if(v=="C")CC();
      if(v=="D")DD();
   }
   arr.shift();
   arr.pop();
   console.log(arr.join("").replace(/0/g,"#"));
}