var a=function(b){if(!b){return 0;}if(!b.left){return 1+a(b.right);}if(!b.right){return 1+a(b.left);}return 1+Math.min(a(b.left),a(b.right));};const solve=b=>a(b);
