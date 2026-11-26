function main(input) {
  const N = parseInt(input, 10);
  const C = Math.floor(100 / 4);
  const D = Math.floor(100 / 7);
  let result = 'No';
  
  for(let i = 0; i <= C; i++) {
  	for(let j = 0; j <= D; j++) {
      if (N === (i * 4) + (j * 7)) {
        result = 'Yes';
      }
    }
  }
  
  console.log(result);
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'));