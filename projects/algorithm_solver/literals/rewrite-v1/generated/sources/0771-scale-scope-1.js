function solve(a,b){const c={};for(const b of a){const a=h(b);c[a]=true;}let d=0;for(const a of b){const b=h(a);if(b in c){d+=1;}}return d;}function h(a){return'$'+a;}
