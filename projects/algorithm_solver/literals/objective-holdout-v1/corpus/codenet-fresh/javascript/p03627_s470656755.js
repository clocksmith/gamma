console.log((args=>{
  const [[N],A] = args.trim().split('\n').map(r=>r.split(' ').map(v=>v|0));
  const a = new Map();
  for ( let i = 0; i < N; i++ ) {
    a.set(A[i],(a.get(A[i])|0)+1);
  }
  const e = [];
  for ( const [k,v] of a ) {
    if ( v >= 2 ) e.push(k);
    if ( v >= 4 ) e.push(k);
  }
  if ( e.length < 2 ) return '0';
  e.sort((a,b)=>b-a);
  return `${BigInt(e[0])*BigInt(e[1])}`;
})(require('fs').readFileSync('/dev/stdin', 'utf8')));
