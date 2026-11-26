function main(input) {
  const arr = input.split(" ")
  const x = Math.ceil(arr[0] / arr[1]) * arr[2];
  const y = Math.ceil(arr[0] / arr[3]) * arr[4];

  x > y ? console.log(y) : console.log(x);
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));
