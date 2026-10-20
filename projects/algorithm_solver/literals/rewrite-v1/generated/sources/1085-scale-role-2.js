function solve(a){let b=Math.min(...a);let r=0;while(b){r+=(b%10+10)%10;b=Math.floor(b/10);}return r&1^1;}
