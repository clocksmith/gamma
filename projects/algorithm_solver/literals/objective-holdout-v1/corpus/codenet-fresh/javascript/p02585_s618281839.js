console.log((args=>{
  const [[N,K],P,C] = args.trim().split`\n`.map(r=>r.split` `.map(v=>v|0));
  let m = P.map((p,i)=>[p-1,BigInt(C[i]),BigInt(C[i])]);
  const op = (x,y) => x.map(([a,b,c])=>[
    y[a][0],
    b + y[a][1],
    (c<b+y[a][2])?b+y[a][2]:c
  ]);
  let x = P.map((p,i)=>[p-1,BigInt(C[i]),BigInt(Math.max(0,C[i]))]);
  let max = BigInt(-2e18);
  let n = K - 1;
  while(n>0) {
    if ( n&1 ) m = op(m,x);
    x = op(x,x);
    n >>= 1;
  }
  for ( let i = 0; i < N; i++ ) if ( max < m[i][2] ) max = m[i][2];
  return `${max}`;
})(require('fs').readFileSync('/dev/stdin','utf8')));
