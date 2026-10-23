// Independent decoder: recursive prefix arity, expression/type/child-span checks, exact packet framing.
const fs=require('node:fs'),crypto=require('node:crypto'),acorn=require('/usr/share/nodejs/acorn');
const hash=b=>crypto.createHash('sha256').update(b).digest();
function expression(text){
 const node=acorn.parseExpressionAt(text,0,{ecmaVersion:2022,preserveParens:true});
 if(node.start!==0||node.end!==text.length)throw Error('operand is not one complete expression');return node;
}
function decode(db,packet){
 if(db.subarray(0,4).toString()!=='EXD1'||packet.subarray(0,4).toString()!=='EXB1')throw Error('magic');
 const entries=JSON.parse(db.subarray(4).toString()),width=packet[4],count=packet.readUInt32BE(37);
 if(![7,8].includes(width)||entries.length>2**width||!packet.subarray(5,37).equals(hash(db)))throw Error('dictionary/width');
 if(packet.length!==41+Math.ceil(count*width/8))throw Error('length');
 const pad=(8-count*width%8)%8;if(pad&&(packet.at(-1)&((1<<pad)-1)))throw Error('padding');
 const ids=[];let value=0,bits=0;
 for(const byte of packet.subarray(41)){
  value=(value<<8)|byte;bits+=8;
  while(bits>=width&&ids.length<count){bits-=width;const id=(value>>bits)&((1<<width)-1);if(id>=entries.length)throw Error('unused code');ids.push(id);}
 }
 let cursor=0;
 function read(asExpression,depth){
  if(depth>8||cursor>=ids.length)throw Error('depth/truncated operand');
  const entry=entries[ids[cursor++]];
  if(entry[0]==='L'){if(typeof entry[1]!=='string'||!entry[1])throw Error('literal');if(asExpression)expression(entry[1]);return entry[1];}
  if(entry[0]!=='C')throw Error('entry kind');
  const spec=entry[1];if(!spec||spec.paths.length<1||spec.paths.length>3||spec.parts.length!==spec.paths.length+1)throw Error('arity');
  const fixed=spec.parts.reduce((s,x)=>s+Buffer.byteLength(x),0);
  if(spec.parts.some(p=>typeof p!=='string')||fixed<1||fixed>32)throw Error('fixed text');
  let text=spec.parts[0],spans=[];
  for(let i=0;i<spec.paths.length;i++){let child=read(true,depth+1);spans.push([text.length,text.length+child.length]);text+=child+spec.parts[i+1];}
  const node=expression(text);
  for(const [key,value] of Object.entries(spec.fields))if(node[key]!==value)throw Error('constructor result type');
  for(let i=0;i<spec.paths.length;i++){
   let child=node;for(const key of spec.paths[i]){if(!child||!Object.hasOwn(child,key))throw Error('child path');child=child[key];}
   if(child.start!==spans[i][0]||child.end!==spans[i][1])throw Error('precedence/child boundary');
  }
  return text;
 }
 let result='';while(cursor<ids.length)result+=read(false,0);return result;
}
if(require.main===module){const input=JSON.parse(fs.readFileSync(0,'utf8')),db=Buffer.from(input.dictionary,'base64');const out={};for(const [id,b64] of Object.entries(input.packets))out[id]=decode(db,Buffer.from(b64,'base64'));process.stdout.write(JSON.stringify(out));}
module.exports={decode};
