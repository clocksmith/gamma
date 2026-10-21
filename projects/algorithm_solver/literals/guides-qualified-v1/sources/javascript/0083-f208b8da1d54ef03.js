function solve(a){let b=a;while(b!==null&&b.next!==null){if(b.val===b.next.val){b.next=b.next.next;}else{b=b.next;}}return a;}
