'use strict';
// Source-free JavaScript counterpart of the existing Q indexed-pool primitives.
function materialize(pid,packet,factory){
 const nodes=packet.values.map(value=>new factory(value));
 if([129,144].includes(pid)){for(let i=0;i<nodes.length;i++){nodes[i].left=packet.left[i]===null?null:nodes[packet.left[i]];nodes[i].right=packet.right[i]===null?null:nodes[packet.right[i]];}return [packet.root===null?null:nodes[packet.root],nodes];}
 if(pid===133){for(let i=0;i<nodes.length;i++)nodes[i].neighbors=packet.neighbors[i].map(j=>nodes[j]);return [packet.root===null?null:nodes[packet.root],nodes];}
 for(let i=0;i<nodes.length;i++)nodes[i].next=i+1<nodes.length?nodes[i+1]:[141,142].includes(pid)&&packet.pos!==-1?nodes[packet.pos]:null;
 if(pid===138)for(let i=0;i<nodes.length;i++)nodes[i].random=packet.random[i]===null?null:nodes[packet.random[i]];
 return [nodes.length?nodes[0]:null,nodes];
}
function snapshot(pid,nodes){
 const index=new Map(nodes.map((node,i)=>[node,i]));if(index.size!==nodes.length)throw Error('duplicate original identity');
 const reference=node=>{if(node===null)return null;if(!index.has(node))throw Error('edge outside declared nodepool');return index.get(node);};
 const fields=[129,144].includes(pid)?['left','right']:pid===133?['neighbors']:pid===138?['next','random']:['next'];
 return nodes.map(node=>{const row={value:node.val};for(const field of fields){if(field==='neighbors'){if(!Array.isArray(node[field]))throw Error('neighbor container');row[field]=node[field].map(reference);}else row[field]=reference(node[field]);}return row;});
}
function originalEntry(result,nodes){if(result===null)return null;const index=nodes.indexOf(result);if(index<0)throw Error('returned clone instead of original identity');return index;}
function reordered(head,nodes,result){
 if(result!==undefined)throw Error('reorderList must return undefined');const index=new Map(nodes.map((node,i)=>[node,i])),seen=new Set(),order=[];
 for(let current=head;current!==null;current=current.next){if(!index.has(current)||seen.has(current))throw Error('new node or cycle in reordered result');seen.add(current);order.push(index.get(current));}
 if(order.length!==nodes.length)throw Error('lost original nodes');return {return:null,original_identity_order:order,values:order.map(i=>nodes[i].val)};
}
function clonePool(pid,result,originals){
 if(result===null){if(originals.length)throw Error('missing clone root');return [];}
 const inputs=new Set(originals),seen=new Set(),pool=[],pending=[result];
 for(let i=0;i<pending.length;i++){const node=pending[i];if(inputs.has(node))throw Error('clone aliases input identity');if(seen.has(node))continue;seen.add(node);pool.push(node);const following=pid===133?node.neighbors:[node.next,node.random];for(const child of following)if(child!==null)pending.push(child);if(pool.length>originals.length)throw Error('too many clone identities');}
 if(pool.length!==originals.length)throw Error('clone nodecount mismatch');return pool;
}
module.exports={materialize,snapshot,originalEntry,reordered,clonePool};
