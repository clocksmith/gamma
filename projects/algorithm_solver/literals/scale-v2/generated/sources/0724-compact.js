function solve(a){let b=0;for(const d of a){b+=d;}let c=0;for(let e=0;e<a.length;e+=1){b-=a[e];if(c===b){return e;}c+=a[e];}return-1;}
