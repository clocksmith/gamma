function main(input) {
  const args = input.split('\n');
  const [N, X] = args[0].split(' ');
  const L = args[1].split(' ');
  const n = Number(N);
  let count = 0;
  const array = [0];
  for (let i = 0; i < n; i++) {
    array.push(count += Number(L[i]));
   }
  for (let i = 0; i < array.length; i++) {
    if (array[i] > X) {
      console.log(i)
      return
    }
  }
  console.log(array.length)
  return; 
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));