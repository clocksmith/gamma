// Independent nonrecursive arity decoder. Complete dictionary metadata is charged.
const fs=require('node:fs'),crypto=require('node:crypto'),acorn=require('/usr/share/nodejs/acorn');
const kinds=new Set(['ForStatement','ForOfStatement','ForInStatement','WhileStatement','DoWhileStatement','IfStatement','ReturnStatement','VariableDeclaration','ExpressionStatement','AssignmentExpression','CallExpression','BinaryExpression','LogicalExpression','ConditionalExpression','NewExpression','MemberExpression','ArrayExpression','ObjectExpression','UnaryExpression','UpdateExpression']);
function id(name){if(typeof name!=='string'||!/^[A-Za-z_$][A-Za-z0-9_$]*$/.test(name))return false;
 try{const n=acorn.parse('function __arg('+name+'){}',{ecmaVersion:2022}).body[0].params;return n.length===1&&n[0].type==='Identifier'&&n[0].name===name;}catch{return false;}}
function shape(text,kind,holes){try{let n,shift=0;if(kind.endsWith('Statement')||kind==='VariableDeclaration'){
 const prefix='function __decoded(){';shift=prefix.length;const body=acorn.parse(prefix+text+'}',{ecmaVersion:2022}).body[0].body.body;if(body.length!==1)return false;n=body[0];
 }else{n=acorn.parseExpressionAt(text,0,{ecmaVersion:2022});if(n.end!==text.length)return false;}
 if(n.type!==kind)return false;const identifiers=new Set();
 function walk(x){if(x.type==='Identifier')identifiers.add(JSON.stringify([x.start-shift,x.end-shift,x.name]));
  for(const v of Object.values(x))if(Array.isArray(v)){for(const c of v)if(c&&typeof c.type==='string')walk(c);}else if(v&&typeof v.type==='string')walk(v);}
 walk(n);return holes.every(h=>identifiers.has(JSON.stringify(h)));}catch{return false;}}

function decode(dictionary,packet){
 if(dictionary.subarray(0,4).toString()!=='ITD1')throw Error('dictionary magic');
 const entries=JSON.parse(dictionary.subarray(4).toString('utf8'));
 if(!Array.isArray(entries)||entries.length<1||entries.length>256||new Set(entries.map(x=>JSON.stringify(x))).size!==entries.length)throw Error('dictionary size/duplicates');
 for(const e of entries){
  if(!Array.isArray(e)||e.length!==2)throw Error('entry shape');
  if(e[0]==='L'){if(typeof e[1]!=='string'||!e[1]||!/^[\x00-\x7f]*$/.test(e[1]))throw Error('literal');}
  else if(e[0]==='C'){const s=e[1];if(!s||!kinds.has(s.kind)||!Number.isInteger(s.arity)||s.arity<1||s.arity>4||!Array.isArray(s.parts)||!Array.isArray(s.uses)||s.parts.length!==s.uses.length+1||s.uses.length>16||s.uses.length<s.arity||s.parts.some(x=>typeof x!=='string'||!/^[\x00-\x7f]*$/.test(x))||s.uses.some(x=>!Number.isInteger(x)||x<0||x>=s.arity)||new Set(s.uses).size!==s.arity||s.parts.reduce((a,b)=>a+b.length,0)<2||s.parts.reduce((a,b)=>a+b.length,0)>96)throw Error('constructor');}
  else throw Error('entry type');
 }
 if(packet.length<41||packet.subarray(0,4).toString()!=='ITB1'||packet[4]!==8||!crypto.createHash('sha256').update(dictionary).digest().equals(packet.subarray(5,37)))throw Error('packet header/hash');
 const count=packet.readUInt32BE(37);if(packet.length!==41+count)throw Error('packet length');
 let offset=41,out='';const expansions=[];
 while(offset<packet.length){const e=entries[packet[offset++]];if(!e)throw Error('unknown ID');
  if(e[0]==='L'){out+=e[1];}
  else {const s=e[1],args=[];for(let i=0;i<s.arity;i++){if(offset>=packet.length)throw Error('truncated arguments');const arg=entries[packet[offset++]];if(!arg||arg[0]!=='L'||!id(arg[1]))throw Error('identifier argument required');args.push(arg[1]);}
   let expansion=s.parts[0];const holes=[];for(let i=0;i<s.uses.length;i++){const name=args[s.uses[i]];holes.push([expansion.length,expansion.length+name.length,name]);expansion+=name+s.parts[i+1];}if(!shape(expansion,s.kind,holes))throw Error('constructor AST shape');expansions.push({text:expansion,free:expansion.length-args.reduce((a,b)=>a+b.length,0)});out+=expansion;}
  if(out.length>4*1024*1024)throw Error('output bound');
 }
 const ast=acorn.parse(out,{ecmaVersion:2022}),bodies=new Set([out]);let found=false;
 for(const n of ast.body){const f=[];if(n.type==='FunctionDeclaration'&&n.id?.name==='solve')f.push(n);
  if(n.type==='VariableDeclaration')for(const d of n.declarations)if(d.id.name==='solve'&&['FunctionExpression','ArrowFunctionExpression'].includes(d.init?.type))f.push(d.init);
  for(const fn of f){found=true;bodies.add(out.slice(fn.start,fn.end));bodies.add(out.slice(fn.body.start,fn.body.end));if(fn.body.type==='BlockStatement')bodies.add(out.slice(fn.body.start+1,fn.body.end-1).trim());}}
 if(!found||expansions.some(e=>e.free*2>=out.length||bodies.has(e.text)))throw Error('whole-solution template');
 return out;
}
if(require.main===module){const input=JSON.parse(fs.readFileSync(0,'utf8')),dict=Buffer.from(input.dictionary,'base64');process.stdout.write(JSON.stringify(Object.fromEntries(Object.entries(input.packets).map(([id,p])=>[id,decode(dict,Buffer.from(p,'base64'))]))));}
module.exports={decode};
