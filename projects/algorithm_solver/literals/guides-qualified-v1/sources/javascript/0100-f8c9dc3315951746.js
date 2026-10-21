var a=function(b,c){if(!b&&!c)return true;if(b&&c){return b.val===c.val&&a(b.left,c.left)&&a(b.right,c.right);}return false;};function solve(d,e){return a(d,e);}
