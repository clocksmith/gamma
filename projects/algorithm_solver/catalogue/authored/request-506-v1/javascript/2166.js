/* Original candidate for LeetCode 2166. Contract: https://leetcode.com/problems/design-bitset/
Development tests only; not admitted or independently qualified.
Batch adapter solve(operations, arguments) follows Bitset class-call arrays.
Complexity: O(1) operations except O(size) toString; O(size+output) space */
"use strict";
function solve(operations,args){const size=args[0][0],bits=new Uint8Array(size),out=[null];let flipped=0,ones=0;for(let t=1;t<operations.length;t++){let op=operations[t],a=args[t],result=null;if(op==='fix'||op==='unfix'){let i=a[0],want=op==='fix'?1:0,old=bits[i]^flipped;if(old!==want){bits[i]^=1;ones+=want?1:-1;}}else if(op==='flip'){flipped^=1;ones=size-ones;}else if(op==='all')result=ones===size;else if(op==='one')result=ones>0;else if(op==='count')result=ones;else if(op==='toString')result=Array.from(bits,b=>b^flipped).join('');out.push(result);}return out;}
module.exports = solve;
