const assert=require('node:assert/strict'),vm=require('node:vm');
const {alternatives}=require('./alternatives.cjs');
const alphabet=Array.from({length:95},(_,i)=>String.fromCharCode(i+32)).concat('\n');
function observe(source,arg){
 const code=source+';const arg='+arg+';let output;try{output={value:solve(arg)}}catch(e){output={error:e.name,message:e.message}};JSON.stringify({output,arg},(k,v)=>typeof v==="bigint"?{bigint:String(v)}:typeof v==="undefined"?{undefined:true}:typeof v==="number"&&(!Number.isFinite(v)||Object.is(v,-0))?{number:String(v),negativeZero:Object.is(v,-0)}:v)';
 return vm.runInNewContext(code,{}, {timeout:100});
}
let checked=0;
function equivalent(source,args,expectedKind){
 const rows=alternatives(source,alphabet,'combined',256).proposals;
 if(expectedKind)assert(rows.some(r=>r.kind===expectedKind));
 for(const r of rows)for(const arg of args){assert.equal(observe(r.text,arg),observe(source,arg),r.kind);checked++;}
 return rows;
}
// All compound arithmetic operators, including coercion, signed zero and BigInt.
for(const op of ['+','-','*','/','%','**','<<','>>','>>>','&','|','^']){
 equivalent('function solve(a){let x=a[0],y=a[1];x'+op+'=y;return x}', ['[4,2]','[-0,2]','[4n,2n]','["4",2]'],'expand_compound');
 equivalent('function solve(a){let x=a[0],y=a[1];x=x'+op+'y;return x}', ['[4,2]','[-0,2]','[4n,2n]','["4",2]'],'contract_compound');
}
// RHS rebinds the target; both forms must read its old value before evaluating RHS.
equivalent('function solve(a){let x=3;x+=(x=a);return x}', ['4','"4"','4n'],'expand_compound');
equivalent('function solve(a){let log=[];let x={valueOf(){log.push("left");return 3}},y={valueOf(){log.push("right");return 4}};x+=y;return [x,log]}',['0'],'expand_compound');
// Discarded values only: postfix used by return/condition/assignment stays unchanged.
equivalent('function solve(a){let x=a;for(x++;x<5;x++){void x++;}return x}',['0','1n','"1"'],'discarded_update');
assert(!alternatives('function solve(a){return a++}',alphabet).proposals.some(r=>r.kind==='discarded_update'));
assert(!alternatives('function solve(a){if(a++)return 1;return 0}',alphabet).proposals.some(r=>r.kind==='discarded_update'));
// Side-effectful conditions run once, only the selected branch runs, and scope stays braced.
equivalent('function solve(a){let x=0;if(a[x++]){let y=3;return [x,y]}else{let y=4;return [x,y]}}',['[true]','[false]','[{}]'],'invert_if');
equivalent('function solve(a){let x=0;return a[x++]?[x,a.push(1)]:[x,a.push(2)]}',['[true]','[false]'],'invert_conditional');
equivalent('function solve(a){let x=0,y=0;outer:while(x++<a){if(x===2)continue outer;y+=x;if(x===4)break;}return [x,y]}',['0','1','5'],'while_to_for');
equivalent('function solve(a){let x=0;for(;;){if(x++>=a)break;}return x}',['0','3'],'for_to_while');
// Unsafe reflection/eval and member-target compounds stay outside the proposal family.
assert(alternatives('function solve(a){return solve.toString()}',alphabet).unsupported);
assert(alternatives('function solve(a){return eval(a)}',alphabet).unsupported);
assert(!alternatives('function solve(a){a.x+=1;return a}',alphabet).proposals.some(r=>r.kind==='expand_compound'));
assert(!alternatives('function solve(a){a&&=1;return a}',alphabet).proposals.some(r=>r.kind==='expand_compound'));
// Inferred names stay unchanged when assignment RHS is an anonymous function.
equivalent('function solve(a){let x=1;x+=()=>1;return typeof x}',['0'],'expand_compound');
const source='function solve(a){let x=a;x+=1;return x}';
const proposal=alternatives(source,alphabet).proposals.find(r=>r.kind==='expand_compound');
assert(proposal);assert(!alternatives(source,alphabet.concat(proposal.text)).proposals.some(r=>r.text===proposal.text));
assert(alternatives('function solve(a){let x=a;x++;x--;return x}',alphabet,'arithmetic',1).truncated);
// Implicit function-source observation and arguments.callee must not be changed.
assert.equal(alternatives('function solve(a){let x=a;x++;return ""+solve}',alphabet).proposals.length,0);
assert(alternatives('function solve(a){let x=a;x++;return arguments.callee+""}',alphabet).unsupported);
const escaped='function solve(a){let f=()=>{let x=a;x++;return x};return String(f)}';
assert.equal(alternatives(escaped,alphabet).proposals.length,0);
// Direct nested callees and IIFEs remain eligible; callback source bodies do not.
equivalent('function solve(a){function f(x){x++;return x}return f(a)}',['1','2n'],'discarded_update');
equivalent('function solve(a){return (()=>{let x=a;x++;return x})()}',['1','2n'],'discarded_update');
console.log(JSON.stringify({passed:true,independent_observations:checked}));
