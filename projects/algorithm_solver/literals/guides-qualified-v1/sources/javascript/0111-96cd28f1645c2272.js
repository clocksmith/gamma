var a=function(a){return fold(a,(a,b,c)=>{if(!a.left){return 1+c;}if(!a.right){return 1+b;}return 1+Math.min(b,c);});};function solve(b){return a(b);}
function fold(node,step){return node?step(node,fold(node.left,step),fold(node.right,step)):0;}
