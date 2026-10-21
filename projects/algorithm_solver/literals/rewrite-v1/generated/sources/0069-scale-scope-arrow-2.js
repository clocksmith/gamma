const solve=a=>{const b=BigInt(a);let c=0n;let d=b;let e=0n;while(c<=d){const a=c+(d-c)/2n;if(a===0n||a<=b/a){e=a;c=a+1n;}else{d=a-1n;}}return e<=BigInt(Number.MAX_SAFE_INTEGER)?Number(e):e;};
