function Main(input) {
  input = input.replace(/\n/g, ' ');
  input = input.split(" ");
  var A = Number(input[0]);
  if(400<=A && A<=599){
    console.log(8);
  }else
  if(600<=A && A<=799){
    console.log(7);
  }else
  if(800<=A && A<=999){
    console.log(6);
  }else
  if(1000<=A && A<=1199){
    console.log(5);
  }else
  if(1200<=A && A<=1399){
    console.log(4);
  }else
  if(1400<=A && A<=1599){
    console.log(3);
  }else
  if(1600<=A && A<=1799){
    console.log(2);
  }else
  if(1800<=A && A<=1999){
    console.log(1);
  }
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));