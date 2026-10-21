var a=function(a){const b=a=>{if(!a){return 0;}const c=b(a.left);const d=b(a.right);if(c==-1||d==-1||Math.abs(c-d)>1){return-1;}return 1+Math.max(c,d);};return b(a)>=0;};const solve=b=>a(b);
