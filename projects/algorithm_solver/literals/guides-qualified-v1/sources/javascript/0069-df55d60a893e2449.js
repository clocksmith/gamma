function solve(a){const b=BigInt(a);let c=0n;let d=b;let e=0n;while(c<=d){const f=c+(d-c)/2n;if(f===0n||f<=b/f){e=f;c=f+1n;}else{d=f-1n;}}return e<=BigInt(Number.MAX_SAFE_INTEGER)?Number(e):e;}
