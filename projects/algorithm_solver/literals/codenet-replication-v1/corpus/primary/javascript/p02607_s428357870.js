function Main(input) {
  let lines = input.split("\n");
  const count = parseInt(lines[0]);
  lines = lines[1].split(" ");
  let total = 0;
  for(let i = 0; i < count; i++){
  	if((i+1)%2 === 0) continue;
    if(parseInt(lines[i])%2 !== 0) total++;
  }
  console.log(total);
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));