function Main(input){
  input = input.split("\n");
  
  var N = parseInt(input[0]);
  var A = parseInt(input[1]);
  
  if(N%500 <= A){
    console.log("Yes");
  }else{
    console.log("No");
  }
}
 
Main(require("fs").readFileSync("/dev/stdin", "utf8"));