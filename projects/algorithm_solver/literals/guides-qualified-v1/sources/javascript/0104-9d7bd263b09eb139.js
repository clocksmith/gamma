var a=function(b){if(!b)return 0;const c=a(b.left);const d=a(b.right);return 1+Math.max(c,d);};const solve=b=>a(b);
