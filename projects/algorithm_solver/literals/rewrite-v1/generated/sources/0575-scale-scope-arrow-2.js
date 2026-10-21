const solve=a=>{const b=h(a);const c=Math.floor(a.length/2);if(b<c){return b;}return c;};function h(a){const b={};let c=0;for(const d of a){if(b[d]!==true){b[d]=true;c+=1;}}return c;}
