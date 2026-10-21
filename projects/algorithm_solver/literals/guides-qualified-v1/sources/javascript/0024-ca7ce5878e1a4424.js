function solve(a){const b={next:a};let c=b;while(c.next&&c.next.next){const a=c.next;const b=a.next;a.next=b.next;b.next=a;c.next=b;c=a;}return b.next;}
