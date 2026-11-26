function Main(input) {
  input = input.split("\n");
  var T = input[0].split(" ");
  var A = input[1].split(" ");
  var B = input[2].split(" ");
  var T0 = T[0];
  var T1 = T[1];
  var A0 = A[0];
  var A1 = A[1];
  var B0 = B[0];
  var B1 = B[1];
  var Ma=T0*(A0-B0);
  var Mb=(T1*A1+Ma)-(T1*B1);
if(Math.sign(Ma)==Math.sign(Mb)){
  console.log(0);
}else if(Mb==0){
  console.log("infinity");
}else{
  Ma = Math.abs(Ma);
  Mb = Math.abs(Mb);
  if(Ma%Mb==0){
    console.log((Ma/Mb)*2);
  }else{
    console.log(Math.ceil(Ma/Mb)*2-1);
  }
}
}Main(require("fs").readFileSync("/dev/stdin", "utf8"));