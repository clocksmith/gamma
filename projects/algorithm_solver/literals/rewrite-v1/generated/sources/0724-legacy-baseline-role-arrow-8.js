const solve=a=>{let b=a.reduce((a,b)=>a+b,0);let r=0;return a.findIndex(a=>{b-=a;const c=r===b;r+=a;return c;});};
