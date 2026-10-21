function solve(a){const b={next:a};let c=b;while(c.next&&c.next.next){const d=c.next;const e=d.next;d.next=e.next;e.next=d;c.next=e;c=d;}return b.next;}
