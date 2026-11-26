const main = input => {
  const inputArray = input.split('\n');
  const n = parseInt(inputArray[0], 10);
  const a = inputArray[1].split(' ').map(x => parseInt(x, 10));

  // 全てのxorを計算
  const allxor = a.reduce((prev, current, index, array) => prev ^ current);
  // console.log(allxor);
  let ret = '';
  
  for (let ai of a) {
    ret += (allxor ^ ai) + ' ';
  }
  console.log(ret.trim());
}

main(require("fs").readFileSync("/dev/stdin", "utf8"));
