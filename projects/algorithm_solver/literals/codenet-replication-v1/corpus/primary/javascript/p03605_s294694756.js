function Main(input) {
  input = input.trim()
  input = input.split("").map(Number);
if(input[0]==9||input[1]==9){
console.log("Yes")
}else{
console.log("No")
}
}Main(require("fs").readFileSync("/dev/stdin", "utf8"));
