const fs=require('fs'),path=require('path');
function linked(a){let head=null;for(let i=a.length-1;i>=0;i--)head={val:a[i],next:head};return head;}
function tree(a){if(!a.length||a[0]===null)return null;let root={val:a[0],left:null,right:null},q=[root],i=1;for(let j=0;j<q.length&&i<a.length;j++){for(const side of ['left','right']){if(i<a.length&&a[i]!==null){q[j][side]={val:a[i],left:null,right:null};q.push(q[j][side]);}i++;}}return root;}
function flat(root){if(!root)return [];let q=[root],out=[];for(let i=0;i<q.length;i++){let n=q[i];out.push(n?n.val:null);if(n)q.push(n.left,n.right);}while(out.length&&out.at(-1)===null)out.pop();return out;}
let cases=JSON.parse(fs.readFileSync(0,'utf8'));let out=[];
for(const c of cases){let args=c.args;if([2095,2130].includes(c.id))args[0]=linked(args[0]);if([2265,2415].includes(c.id))args[0]=tree(args[0]);let ans=require(path.join(__dirname,'../javascript',c.id+'.js'))(...args);if(c.id===2095){let a=[];while(ans){a.push(ans.val);ans=ans.next;}ans=a;}if(c.id===2415)ans=flat(ans);out.push(ans);}
process.stdout.write(JSON.stringify(out,(_,v)=>typeof v==='bigint'?v.toString():v));
