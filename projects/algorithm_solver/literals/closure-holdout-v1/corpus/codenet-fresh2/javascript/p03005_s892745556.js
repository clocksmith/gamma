function Main(input) {
  input = input.split(" ");
  const N = parseInt(input[0],10);
  const K = parseInt(input[1],10);

  if(K ===1){
    console.log(0);
    return;
  }
  console.log(N-K);
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));