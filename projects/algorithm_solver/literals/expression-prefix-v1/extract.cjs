// Encoder-side AST instances. No source execution.
const fs=require('node:fs'),acorn=require('/usr/share/nodejs/acorn');
const expression=new Set(['Identifier','Literal','ThisExpression','ArrayExpression','ObjectExpression','FunctionExpression','ArrowFunctionExpression','ClassExpression','MemberExpression','CallExpression','NewExpression','UnaryExpression','UpdateExpression','BinaryExpression','LogicalExpression','AssignmentExpression','ConditionalExpression','SequenceExpression','TemplateLiteral','TaggedTemplateExpression','ParenthesizedExpression','ChainExpression']);
const at=(n,p)=>p.reduce((x,k)=>x?.[k],n);
function children(n){return Object.values(n).flatMap(v=>Array.isArray(v)?v.filter(x=>x&&typeof x.type==='string'):v&&typeof v.type==='string'?[v]:[]);}
function paths(n){
 if(['BinaryExpression','LogicalExpression','AssignmentExpression'].includes(n.type))return [['left'],['right']];
 if(['UnaryExpression','UpdateExpression'].includes(n.type))return [['argument']];
 if(n.type==='ParenthesizedExpression')return [['expression']];
 if(n.type==='ConditionalExpression')return [['test'],['consequent'],['alternate']];
 if(n.type==='MemberExpression')return n.computed?[['object'],['property']]:[['object']];
 if(n.type==='CallExpression'&&n.arguments.length<=3&&!n.arguments.some(x=>x.type==='SpreadElement')){
  let p=[];
  if(n.callee.type==='MemberExpression'&&!n.callee.computed){
   if(!(n.callee.object.type==='Identifier'&&['Math','Number','String','Array','Object','JSON'].includes(n.callee.object.name)))p=[['callee','object']];
  }else p=[['callee']];
  p.push(...n.arguments.map((_,i)=>['arguments',i]));return p;
 }
 return [];
}
function extract(text){
 const ast=acorn.parse(text,{ecmaVersion:2022,preserveParens:true});const nodes=[];
 function walk(n){
  if(expression.has(n.type)){
   const p=paths(n),holes=p.map(x=>at(n,x));let spec=null;
   if(p.length>=1&&p.length<=3&&holes.every(x=>x&&expression.has(x.type))&&holes.every((x,i)=>i===0||x.start>=holes[i-1].end)){
    const parts=[];let off=n.start;
    for(const h of holes){parts.push(text.slice(off,h.start));off=h.end;}parts.push(text.slice(off,n.end));
    const fixed=parts.reduce((s,x)=>s+Buffer.byteLength(x),0),fields={type:n.type};
    for(const k of ['operator','prefix','computed','optional'])if(n[k]!==undefined)fields[k]=n[k];
    if(fixed>0&&fixed<=32&&fixed<Buffer.byteLength(text)/2){
     // Contextual wrappers (notably optional chains) must not masquerade as another result kind.
     try{
      const piece=text.slice(n.start,n.end),parsed=acorn.parseExpressionAt(piece,0,{ecmaVersion:2022,preserveParens:true});
      if(parsed.start===0&&parsed.end===piece.length&&Object.entries(fields).every(([k,v])=>parsed[k]===v)&&p.every((path,i)=>{
       const child=at(parsed,path);return child?.start===holes[i].start-n.start&&child?.end===holes[i].end-n.start;
      }))spec={fields,paths:p,parts};
     }catch{}
    }
   }
   nodes.push({start:n.start,end:n.end,spec,holes:spec?holes.map(x=>[x.start,x.end]):[]});
  }
  for(const c of children(n))walk(c);
 }
 walk(ast);return nodes.sort((a,b)=>(a.end-a.start)-(b.end-b.start)||a.start-b.start);
}
if(require.main===module){const input=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(Object.fromEntries(Object.entries(input).map(([id,text])=>[id,extract(text)]))));}
module.exports={extract};
