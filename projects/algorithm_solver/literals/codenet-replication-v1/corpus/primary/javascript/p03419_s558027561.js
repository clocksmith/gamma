function Main(input){
  var [a,b] = input.split(" ").map(BigInt);
  console.log(((a==1n||b==1n)?((a==b)?1n:(a==1n)?b-2n:a-2n):a*b-((a-2n)*2n+(b-2n)*2n)-4n).toString())
}Main(require("fs").readFileSync("/dev/stdin", "utf8").trim());
