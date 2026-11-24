console.log((args=>{
  let [X,Y] = args.trim().split(' ').map(BigInt);
  let i = 0;
  do i++; while ( Y >= (X<<=1n) );
  return `${i}`;
})(require('fs').readFileSync('/dev/stdin', 'utf8')));
