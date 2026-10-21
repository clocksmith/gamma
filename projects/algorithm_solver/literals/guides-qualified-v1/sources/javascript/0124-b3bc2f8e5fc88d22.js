var a=function(a){let b=-1001;const c=a=>{return fold(a,(a,c,d)=>{const e=Math.max(0,c);const f=Math.max(0,d);b=Math.max(b,e+f+a.val);return Math.max(e,f)+a.val;});};c(a);return b;};function solve(b){return a(b);}
function fold(node,step){return node?step(node,fold(node.left,step),fold(node.right,step)):0;}
