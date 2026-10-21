function solve(a){let b=0;for(const c of a){b+=c;}let c=0;for(let d=0;d<a.length;d+=1){b-=a[d];if(c===b){return d;}c+=a[d];}return-1;}
