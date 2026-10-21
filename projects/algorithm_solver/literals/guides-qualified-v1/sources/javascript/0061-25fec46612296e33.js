function solve(a,b){if(!a||!a.next||!b){return a;}let c=a,r=1;while(c.next){c=c.next;r++;}b%=r;if(!b){return a;}c.next=a;let d=a;for(let i=1;i<r-b;i++){d=d.next;}const e=d.next;d.next=null;return e;}
