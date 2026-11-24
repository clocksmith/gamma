function Main(input){
var N = input.split("\n")[0];
var value = input.split("\n")[1].split(" ");
var a = 0;
var Max_value = value.sort(function(a,b){
  return a - b;
});
for(i=0;i<=(N-1);i++){
  if(i===0){
    a += new Number(Max_value[i]);
  }else if(i===(N-1)){
    a += new Number(Max_value[i])*Math.pow(2,i-1);
    a = a/Math.pow(2,N-1);
  }else{
    a += new Number(Max_value[i])*Math.pow(2,i-1);
  }
}
  console.log(a);
}
  Main(require('fs').readFileSync('/dev/stdin','utf8'));