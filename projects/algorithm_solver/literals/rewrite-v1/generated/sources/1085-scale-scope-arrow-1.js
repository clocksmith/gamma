const solve=a=>{let b=Math.min(...a);let c=0;while(b){c+=(b%10+10)%10;b=Math.floor(b/10);}return c&1^1;};
