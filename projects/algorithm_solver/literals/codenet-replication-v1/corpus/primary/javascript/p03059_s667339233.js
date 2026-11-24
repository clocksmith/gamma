function Main(input){
  input = input.split("\n");
  inputStr = input[0].split(" ");
  var A = Number.parseInt(inputStr[0]);
  var B = Number.parseInt(inputStr[1]);
  var T = Number.parseInt(inputStr[2]) + 0.5;
  
  console.log(Math.floor(T/A)*B);
  
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));
