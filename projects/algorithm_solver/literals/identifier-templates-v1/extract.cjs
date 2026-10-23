// Exact AST-span identifier templates. No behavioral rewrite or source execution.
const fs=require('node:fs'),acorn=require('/usr/share/nodejs/acorn');
const kinds=new Set(['Identifier','ForStatement','ForOfStatement','ForInStatement','WhileStatement','DoWhileStatement','IfStatement','ReturnStatement','VariableDeclaration','ExpressionStatement','AssignmentExpression','CallExpression','BinaryExpression','LogicalExpression','ConditionalExpression','NewExpression','MemberExpression','ArrayExpression','ObjectExpression','UnaryExpression','UpdateExpression']);
const fixed=new Set(['solve','undefined','Infinity','NaN','Math','Number','Array','Object','JSON','Map','Set','String','Boolean','BigInt','Date','RegExp','console']);
function walk(node,visit,parent=null,key=null){visit(node,parent,key);for(const [k,v] of Object.entries(node))if(Array.isArray(v)){for(const c of v)if(c&&typeof c.type==='string')walk(c,visit,node,k);}else if(v&&typeof v.type==='string')walk(v,visit,node,k);}
function standalone(text,kind){try{let n;if(kind.endsWith('Statement')||kind==='VariableDeclaration'){
 const ast=acorn.parse('function __template(){'+text+'}',{ecmaVersion:2022});const body=ast.body[0].body.body;if(body.length!==1)return false;n=body[0];
 }else{n=acorn.parseExpressionAt(text,0,{ecmaVersion:2022});if(n.end!==text.length)return false;}
 return n.type===kind;}catch{return false;}}
function extract(text){
 if(!/^[\x00-\x7f]*$/.test(text))throw Error('ASCII source required');
 const ast=acorn.parse(text,{ecmaVersion:2022}),candidates=[],excluded=new Set(),bodies=new Set([text]);
 for(const n of ast.body){const f=[];if(n.type==='FunctionDeclaration'&&n.id?.name==='solve')f.push(n);
  if(n.type==='VariableDeclaration')for(const d of n.declarations)if(d.id.name==='solve'&&['FunctionExpression','ArrowFunctionExpression'].includes(d.init?.type))f.push(d.init);
  for(const fn of f){bodies.add(text.slice(fn.start,fn.end));bodies.add(text.slice(fn.body.start,fn.body.end));if(fn.body.type==='BlockStatement')bodies.add(text.slice(fn.body.start+1,fn.body.end-1).trim());}}
 walk(ast,(n,p,k)=>{if(kinds.has(n.type))candidates.push(n);
  if(n.type==='Identifier'&&(text.slice(n.start,n.end)!==n.name||fixed.has(n.name)||(p?.type==='MemberExpression'&&k==='property'&&!p.computed)||(['Property','MethodDefinition'].includes(p?.type)&&k==='key'&&!p.computed)||k==='label'))excluded.add(n.start);});
 const result=[];
 for(const n of candidates){
  const piece=text.slice(n.start,n.end);if(piece.length<2||piece.length>160)continue;
  let spec=null,args=[],freeBytes=0;
  if(!bodies.has(piece)&&standalone(piece,n.type)){
   const ids=new Map();walk(n,x=>{if(x.type==='Identifier'&&!excluded.has(x.start))ids.set(x.start,x)});
   const spans=[...ids.values()].sort((a,b)=>a.start-b.start);const names=[...new Set(spans.map(x=>x.name))];
   if(names.length>=1&&names.length<=4&&spans.length<=16){
    const parts=[],uses=[];let pos=n.start;
    for(const id of spans){parts.push(text.slice(pos,id.start));uses.push(names.indexOf(id.name));pos=id.end;}parts.push(text.slice(pos,n.end));
    const fixedBytes=parts.reduce((s,p)=>s+p.length,0);freeBytes=piece.length-names.reduce((s,x)=>s+x.length,0);
    if(fixedBytes>=2&&fixedBytes<=96&&freeBytes*2<text.length){spec={kind:n.type,parts,uses,arity:names.length};args=names;}
   }
  }
  result.push({start:n.start,end:n.end,spec,args,free_bytes:freeBytes});
 }
 return result;
}
if(require.main===module){const texts=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(Object.fromEntries(Object.entries(texts).map(([id,text])=>[id,extract(text)]))));}
module.exports={extract,standalone};
