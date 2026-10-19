// Existing installed parser/compiler only. No package installation or network.
const fs=require('fs');
const ts=require('/home/x/deco/reploid/node_modules/typescript');
const babel=require('/usr/share/nodejs/@babel/core');
const traverse=require('/usr/share/nodejs/@babel/traverse').default;
const generate=require('/usr/share/nodejs/@babel/generator').default;
const acorn=require('/home/x/deco/reploid/node_modules/acorn');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const compiled=input.typescript?ts.transpileModule(input.source,{compilerOptions:{target:ts.ScriptTarget.ES2020,module:ts.ModuleKind.None,removeComments:true,newLine:ts.NewLineKind.LineFeed},reportDiagnostics:true}):{outputText:input.source,diagnostics:[]};
if(compiled.diagnostics.some(d=>d.category===ts.DiagnosticCategory.Error))throw Error('TypeScript transpilation diagnostics');
const ast=babel.parseSync(compiled.outputText,{sourceType:'script',babelrc:false,configFile:false});
const bindings=new Set();let entry;
traverse(ast,{Scope(path){for(const binding of Object.values(path.scope.bindings))bindings.add(binding);},Function(path){if(path.node.id?.name===input.method||path.parentPath.isVariableDeclarator()&&path.parentPath.node.id.name===input.method)entry=path;}});
if(!entry||entry.node.params.length!==1||entry.node.params[0].type!=='Identifier')throw Error('Unsupported entry signature');
const param=entry.scope.getBinding(entry.node.params[0].name);
const original=generate(ast,{comments:false}).code+'\n';
const ordered=[...bindings].sort((a,b)=>a.identifier.start-b.identifier.start);
if(ordered.some(b=>b.identifier.name==='implementation'||/^p0$|^local\d+$/.test(b.identifier.name)))throw Error('Canonical naming collision');
let next=0;
for(const binding of ordered){const old=binding.identifier.name;const name=old===input.method?'implementation':binding===param?'p0':`local${next++}`;binding.scope.rename(old,name);}
const normalized=generate(ast,{comments:false}).code+'\n';
function counts(source){const tree=acorn.parse(source,{ecmaVersion:2022,sourceType:'script'}),byType={};function visit(v){if(!v||typeof v!=='object')return;if(typeof v.type==='string')byType[v.type]=(byType[v.type]||0)+1;for(const x of Object.values(v)){if(Array.isArray(x))x.forEach(visit);else if(x&&typeof x==='object')visit(x);}}visit(tree);return {total:Object.values(byType).reduce((a,b)=>a+b,0),by_type:byType};}
process.stdout.write(JSON.stringify({original,normalized,original_ast:counts(original),normalized_core_ast:counts(normalized),tools:{typescript:ts.version,babel:babel.version,acorn:acorn.version},type_erasure:input.typescript}));
