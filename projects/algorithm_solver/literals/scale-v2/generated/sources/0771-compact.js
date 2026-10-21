function solve(b,c){const d={};for(const f of b){const g=a(f);d[g]=true;}let e=0;for(const h of c){const i=a(h);if(i in d){e+=1;}}return e;}function a(j){return'$'+j;}
