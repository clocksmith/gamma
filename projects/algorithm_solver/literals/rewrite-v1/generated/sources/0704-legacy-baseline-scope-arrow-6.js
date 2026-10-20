const solve=(a,b)=>{let c=0;let d=a.length;while(c<d){const e=Math.floor((c+d)/2);if(a[e]<b)c=e+1;else d=e;}return a[c]===b?c:-1;};
