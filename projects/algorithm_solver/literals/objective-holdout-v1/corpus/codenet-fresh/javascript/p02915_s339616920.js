(input => {
  const inputAry = [...Array(3)].map(() => Number(input))
  console.log(inputAry.reduce((a,k) => a*k,1))
})(require('fs').readFileSync('/dev/stdin', 'utf8').slice(0,-1));
