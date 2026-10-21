function solve(b,c){const d=a(b,c);if(d<b.length&&b[d]===c){return d;}return-1;}function a(e,f){let g=0;let h=e.length;while(g<h){const i=g+Math.floor((h-g)/2);if(e[i]<f){g=i+1;}else{h=i;}}return g;}
