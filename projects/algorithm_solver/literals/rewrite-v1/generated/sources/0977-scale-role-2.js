function solve(a){const r=[];let n=0;let b=a.length;while(n<b){const c=a[n]*a[n];const d=a[b-1]*a[b-1];if(c>d){r.push(c);n+=1;}else{r.push(d);b-=1;}}r.reverse();return r;}
