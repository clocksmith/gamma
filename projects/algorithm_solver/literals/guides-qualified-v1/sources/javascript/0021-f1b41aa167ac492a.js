function solve(a,b){const c={next:null};let d=c;while(a!=null&&b!=null){if(a.val<=b.val){d.next=a;a=a.next;}else{d.next=b;b=b.next;}d=d.next;}d.next=a??b;return c.next;}
