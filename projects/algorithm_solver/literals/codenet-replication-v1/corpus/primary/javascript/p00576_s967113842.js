var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr= input.trim().split("\n");
var x=arr[1].split(" ").map(Number);
var a=arr[3].split(" ").map(Number);
var box=[];
for(var i=0;i<=2020;i++)box[i]=0;
x.forEach(v=> box[v]=1);
box[2020]=1;
a.forEach(v=>{
   if(box[x[v-1]+1]==0){
      box[x[v-1]]=0;
      x[v-1]++;
      box[x[v-1]]=1;
   }
});
console.log(x.join("\n"));
