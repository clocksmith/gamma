function solve(a,b){let r=0;let c=a.length;while(r<c){const d=Math.floor((r+c)/2);if(a[d]<b)r=d+1;else c=d;}return a[r]===b?r:-1;}
