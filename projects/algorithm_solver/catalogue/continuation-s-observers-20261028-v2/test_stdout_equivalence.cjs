"use strict";
// End-to-end v1/v2 comparison through main(): each observer runs as a child
// process with the protocol's JavaScript flags on the same synthetic program
// and packet, and the test requires byte-identical stdout plus equal exit
// status. Packets include full-size envelopes (T 100000 nodes, S 50000).
// Programs are hand-written synthetic implementations, not numbered
// candidates. This runs without the sandbox's CPU cap: it checks equal
// output, not timing.
const fs=require('fs'),os=require('os'),path=require('path'),crypto=require('crypto'),{spawnSync}=require('child_process');
const LANE=path.basename(__dirname).includes('-t-observers-')?'t':'s';
const V1=path.join(__dirname,'..',`continuation-${LANE}-observers-20261028-v1`);
const FLAGS=['--jitless','--single-threaded','--max-old-space-size=256'];
const TREE_DEFAULT="function TreeNode(val,left,right){this.val=(val===undefined?0:val);this.left=(left===undefined?null:left);this.right=(right===undefined?null:right);}\n";
const TREE_REQUIRED="function TreeNode(val){this.val=val;this.left=null;this.right=null;}\n";
const LIST_DEFAULT="function ListNode(val,next){this.val=(val===undefined?0:val);this.next=(next===undefined?null:next);}\n";
const LIST_REQUIRED="function ListNode(val){this.val=val;this.next=null;}\n";
const P={
 226:TREE_DEFAULT+"function invertTree(root){const s=[root];while(s.length){const n=s.pop();if(!n)continue;const t=n.left;n.left=n.right;n.right=t;s.push(n.left,n.right);}return root;}\nmodule.exports={TreeNode,invertTree};",
 230:TREE_DEFAULT+"function kthSmallest(root,k){const s=[];let c=root;while(c||s.length){while(c){s.push(c);c=c.left;}c=s.pop();if(--k===0)return c.val;c=c.right;}}\nmodule.exports={TreeNode,kthSmallest};",
 234:LIST_DEFAULT+"function isPalindrome(head){let n=0;for(let c=head;c;c=c.next)n++;let c=head;for(let i=0;i<Math.floor((n+1)/2);i++)c=c.next;let prev=null;while(c){const x=c.next;c.next=prev;prev=c;c=x;}let ok=true;for(let a=head,b=prev;b;a=a.next,b=b.next)if(a.val!==b.val){ok=false;break;}let back=null;c=prev;while(c){const x=c.next;c.next=back;back=c;c=x;}let t=head;for(let i=0;i<Math.floor((n+1)/2)-1;i++)t=t.next;if(n>1)t.next=back;return ok;}\nmodule.exports={ListNode,isPalindrome};",
 235:TREE_REQUIRED+"function lowestCommonAncestor(root,p,q){let c=root;while(c){if(p.val<c.val&&q.val<c.val)c=c.left;else if(p.val>c.val&&q.val>c.val)c=c.right;else return c;}return null;}\nmodule.exports={TreeNode,lowestCommonAncestor};",
 236:TREE_REQUIRED+"function lowestCommonAncestor(root,p,q){const parent=new Map([[root,null]]),s=[root];while(s.length){const n=s.pop();for(const c of [n.left,n.right])if(c){parent.set(c,n);s.push(c);}}const seen=new Set();for(let x=p;x;x=parent.get(x))seen.add(x);for(let x=q;x;x=parent.get(x))if(seen.has(x))return x;return null;}\nmodule.exports={TreeNode,lowestCommonAncestor};",
 237:LIST_REQUIRED+"function deleteNode(node){node.val=node.next.val;node.next=node.next.next;}\nmodule.exports={ListNode,deleteNode};",
 199:TREE_DEFAULT+"function rightSideView(root){const out=[];let level=root?[root]:[];while(level.length){out.push(level[level.length-1].val);const next=[];for(const n of level){if(n.left)next.push(n.left);if(n.right)next.push(n.right);}level=next;}return out;}\nmodule.exports={TreeNode,rightSideView};",
 203:LIST_DEFAULT+"function removeElements(head,val){const d=new ListNode(0,head);let c=d;while(c.next){if(c.next.val===val)c.next=c.next.next;else c=c.next;}return d.next;}\nmodule.exports={ListNode,removeElements};",
 206:LIST_DEFAULT+"function reverseList(head){let p=null,c=head;while(c){const n=c.next;c.next=p;p=c;c=n;}return p;}\nmodule.exports={ListNode,reverseList};",
 222:TREE_DEFAULT+"function countNodes(root){let n=0;const s=root?[root]:[];while(s.length){const x=s.pop();n++;if(x.left)s.push(x.left);if(x.right)s.push(x.right);}return n;}\nmodule.exports={TreeNode,countNodes};",
};
// Independent-review reproducers (Proxy on the exported constructor's chain,
// armed by the official call). v2 must match v1 exactly.
const CHAIN_LIST=mode=>"function ListNode(val,next){this.val=(val===undefined?0:val);this.next=(next===undefined?null:next);}\nlet armed=false,count=0,H=null;const MODE='"+mode+"';\nObject.setPrototypeOf(ListNode,new Proxy(Function.prototype,{getPrototypeOf(t){if(armed){count++;if(MODE==='A'&&count>=4)throw Error('trap-reject-'+count);if(MODE==='B'&&count===3)throw Error('trap-once-'+count);if(MODE==='C'&&count===4)H.val=9;}return Reflect.getPrototypeOf(t);}}));\nfunction isPalindrome(head){armed=true;count=0;H=head;const a=[];for(let c=head;c;c=c.next)a.push(c.val);for(let i=0,j=a.length-1;i<j;i++,j--)if(a[i]!==a[j])return false;return true;}\nmodule.exports={ListNode,isPalindrome};";
const CHAIN_TREE="function TreeNode(val,left,right){this.val=(val===undefined?0:val);this.left=(left===undefined?null:left);this.right=(right===undefined?null:right);}\nlet armed=false,count=0;\nObject.setPrototypeOf(TreeNode,new Proxy(Function.prototype,{getPrototypeOf(t){if(armed){count++;if(count>=4)throw Error('trap-reject-'+count);}return Reflect.getPrototypeOf(t);}}));\nfunction countNodes(root){armed=true;count=0;let n=0;const s=root?[root]:[];while(s.length){const x=s.pop();n++;if(x.left)s.push(x.left);if(x.right)s.push(x.right);}return n;}\nmodule.exports={TreeNode,countNodes};";
const chain=n=>({values:Array.from({length:n},(_,i)=>i),left:Array(n).fill(null),right:Array.from({length:n},(_,i)=>i+1<n?i+1:null),root:n?0:null});
const complete=(n,v)=>({values:v||Array.from({length:n},(_,i)=>i),left:Array.from({length:n},(_,i)=>2*i+1<n?2*i+1:null),right:Array.from({length:n},(_,i)=>2*i+2<n?2*i+2:null),root:n?0:null});
const list=(vals)=>({values:vals,next:vals.map((_,i)=>i+1<vals.length?i+1:null),head:vals.length?0:null});
const pal=n=>Array.from({length:n},(_,i)=>Math.min(i,n-1-i)%10);
const T=[
 [235,[[chain(3),0,2],[chain(100000),50000,99999],[chain(3),0,2]]],
 [236,[[complete(3),1,2],[complete(100000),50000,99999],[complete(3),1,2]]],
 [234,[[list(pal(100000))],[list(pal(100000))]]],
 [234,[[list([1,2,1])],[list([1,2])],[{values:[1],next:[0],head:0}],[list(pal(100000))]]],
 [237,[[list(Array.from({length:1000},(_,i)=>i-500)),10],[list([1,2,3]),2],[list([4,5,1,9]),1]]],
 [226,[[complete(100,Array.from({length:100},(_,i)=>i-50))],[complete(0)],[chain(3)]]],
 [230,[[chain(10000),5000],[chain(10000),10001],[chain(3),1]]],
 [234,[[list([1,2,1])],[list(pal(1000))]],CHAIN_LIST('A'),'review A: chain trap throws from 4th armed guard'],
 [234,[[list([1,2,1])],[list(pal(1000))]],CHAIN_LIST('B'),'review B: chain trap throws once at 3rd armed guard'],
 [234,[[list([1,2,1])],[list(pal(1000))]],CHAIN_LIST('C'),'review C: chain trap mutates head at 4th armed guard'],
];
const S=[
 [222,[[complete(50000)],[complete(50000)]]],
 [222,[[complete(0)],[complete(7)],[{values:[1,2],left:[null,null],right:[1,null],root:0}]]],
 [203,[[list(Array.from({length:10000},(_,i)=>1+i%50)),7],[list([7,7,7]),7],[list([]),1]]],
 [206,[[list(Array.from({length:5000},(_,i)=>i-2500))],[list([])],[list([1])]]],
 [199,[[complete(100,Array.from({length:100},(_,i)=>i-50))],[complete(0)]]],
 [222,[[complete(7)],[complete(2000)]],CHAIN_TREE,'review S222: chain trap throws from 4th armed guard'],
];
function run(dir,pid,calls,program){
 const work=fs.mkdtempSync(path.join(os.tmpdir(),'obs-eq-'));
 try{
  for(const f of ['harness.cjs','native_graphs.cjs'])fs.copyFileSync(path.join(dir,f),path.join(work,f));
  fs.writeFileSync(path.join(work,'program.cjs'),program||P[pid]);
  fs.writeFileSync(path.join(work,'inputs.json'),JSON.stringify({schema:`gamma.${LANE}-official-packet.v1`,problem_id:pid,calls:calls.map(args=>({args}))}));
  const res=spawnSync(process.execPath,[...FLAGS,'harness.cjs'],{cwd:work,maxBuffer:64*1024*1024});
  return {status:res.status,signal:res.signal,stdout:res.stdout};
 }finally{fs.rmSync(work,{recursive:true,force:true});}
}
const rows=[];let failed=0;
for(const [pid,calls,program,label] of LANE==='t'?T:S){
 const a=run(V1,pid,calls,program),b=run(__dirname,pid,calls,program),same=a.status===b.status&&a.signal===b.signal&&Buffer.compare(a.stdout,b.stdout)===0;
 const errors=a.stdout.toString().split('\n').filter(l=>l.includes('"error"')).length;
 rows.push({pid,label:label||null,calls:calls.length,stdout_bytes:a.stdout.length,error_rows:errors,stdout_sha256:crypto.createHash('sha256').update(a.stdout).digest('hex'),identical:same});
 if(!same||a.status!==0)failed++;
}
process.stdout.write(JSON.stringify({schema:`gamma.${LANE}-observer-v1-v2-stdout-equivalence.v1`,node:process.version,flags:FLAGS,packets:rows.length,identical:rows.filter(r=>r.identical).length,rows,candidate_executions:0})+'\n');
if(failed)process.exitCode=1;
