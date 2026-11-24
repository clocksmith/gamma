function main(input) {
 
  const n = input.split(" ").map(Number);
  let a = n*800;
  let b = Math.floor(n/15)*200;
  console.log(a-b);
}
main(require("fs").readFileSync("/dev/stdin", "utf8"));