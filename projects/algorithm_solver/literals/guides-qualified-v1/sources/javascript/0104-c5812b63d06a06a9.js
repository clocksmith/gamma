var a=function(a){return fold(a,(a,b,c)=>{const d=b;const e=c;return 1+Math.max(d,e);});};function solve(b){return a(b);}
function fold(node,step){return node?step(node,fold(node.left,step),fold(node.right,step)):0;}
