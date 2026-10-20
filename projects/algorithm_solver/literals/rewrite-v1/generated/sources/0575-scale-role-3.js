function solve(a){const b=h(a);const c=Math.floor(a.length/2);if(b<c){return b;}return c;}function h(a){const m={};let r=0;for(const x of a){if(m[x]!==true){m[x]=true;r+=1;}}return r;}
