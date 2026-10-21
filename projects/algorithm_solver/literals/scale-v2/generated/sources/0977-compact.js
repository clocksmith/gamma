function solve(a){const b=[];let c=0;let d=a.length;while(c<d){const e=a[c]*a[c];const f=a[d-1]*a[d-1];if(e>f){b.push(e);c+=1;}else{b.push(f);d-=1;}}b.reverse();return b;}
