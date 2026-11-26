function main(input) {
  const a = parseInt(input.split(" ")[0], 10);
  const b = parseInt(input.split(" ")[1], 10);
  const c = parseInt(input.split(" ")[2], 10);
  const d = parseInt(input.split(" ")[3], 10);
  if(Math.abs(a-c)<=d||(Math.abs(a-b)<=d&&Math.abs(b-c)<=d)){
    console.log("Yes");
  }else{
    console.log("No");
  }

}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));