const Main = (input) => {
  input = input.split("\n");
  const N = Number(input[0]);
  let cnt = 0;
  let boolean = false;

  for(let i =1; i <= N; i++) {
    const nums = input[i].split(' ');
    const first = Number(nums[0]);
    const second = Number(nums[1]);
    
    if(first === second) {
      cnt++;
      if(cnt >= 3) {
        boolean = true;
      }
    } else {
      cnt = 0;
    }
  }
  if(boolean) {
    console.log('Yes');
  } else {
    console.log('No');
  }
 
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));
// Main(``);