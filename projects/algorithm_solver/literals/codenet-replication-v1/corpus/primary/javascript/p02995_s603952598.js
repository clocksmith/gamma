console.log((args=>{
  const [A,B,C,D] = args.trim().split(' ').map(BigInt);
  const gcd = (a,b) => {while(a)[a,b]=[b%a,a]; return b;};
  const A2B = B - A + 1n;
  const divC = B/C - (A-1n)/C;
  const divD = B/D - (A-1n)/D;
  const CD = C*D/gcd(C,D);
  const divCD = B/CD - (A-1n)/CD;

  return `${A2B - divC - divD + divCD}`
})(require('fs').readFileSync('/dev/stdin', 'utf8')));
