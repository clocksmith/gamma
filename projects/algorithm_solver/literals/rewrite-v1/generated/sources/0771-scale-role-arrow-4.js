const solve=(a,b)=>{const m={};for(const x of a){const a=h(x);m[a]=true;}let r=0;for(const x of b){const a=h(x);if(a in m){r+=1;}}return r;};function h(a){return'$'+a;}
