function main(input) {
  const args = input.split('\n');
  let ary1 = args[0].split(' ').map(n => parseInt(n, 10));
  const N = ary1[0];
  const L = ary1[1];
  let ary = [];
  let ans;
  
  for (let i = 1; i < args.length; i++) {
    a = args[i].split(' ').map(n => parseInt(n, 10));
    if (a[1] <= L) {
      ary.push(a);
    }
  }
  
  for (let i = 0; i < ary.length; i++) {
    if (!ans || ary[i][0] < ans) {
      ans = ary[i][0];
    }
  }
  
  if (!ans) {
    console.log('TLE');
  } else {
    console.log(ans);
  }
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'));