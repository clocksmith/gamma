//let input = "6 20 7";

function main(input){
  input = input.trim();
  let list = input.split(" ");
  let min = parseInt(list[0])-1;
  let max = parseInt(list[1]);
  let a = parseInt(list[2]);
  let dai = Math.floor(max/a);
  let syou = Math.floor(min/a);
  let answer = dai - syou;
  console.log(answer);
}
//main(input);
main(require("fs").readFileSync("/dev/stdin", "utf8"));