function solve(a){const r=[];const b=[];let c=a;while(c!==null||b.length>0){while(c!==null){b.push(c);c=c.left;}c=b.pop();r.push(c.val);c=c.right;}return r;}
