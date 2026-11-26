console.log((args=>{
  const [N,A,B] = args.trim().split` `.map(BigInt);
  if ( (B-A) % 2n === 0n ) return `${(B-A)/2n}`;
  return `${((N-B<A-1n)?N-B:A-1n)+(B-A+1n)/2n}`;
})(require('fs').readFileSync('/dev/stdin', 'utf8')));
