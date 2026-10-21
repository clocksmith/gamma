var a=function(a,b){function c(a,d){if(!a)return false;d+=a.val;if(!a.left&&!a.right&&d==b)return true;return c(a.left,d)||c(a.right,d);}return c(a,0);};function solve(b,c){return a(b,c);}
