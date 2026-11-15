// Development-only executable integer-program oracles. Never a sealed shader claim.
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { validateTasks } from './task_contract.mjs';
const cases = [
  ['stride-sum', 'let s=0; for(let i=2;i<15;i+=3) s+=i; return s;', () => {let s=0;for(let i=2;i<15;i+=3)s+=i;return s;}],
  ['xor-prefix', 'let x=0; for(let i=1;i<=11;i++) x^=i; return x;', () => {let x=0;for(let i=1;i<=11;i++)x^=i;return x;}],
  ['mod-loop', 'let x=3; for(let i=0;i<4;i++) x=(x*2+1)%13; return x;', () => {let x=3;for(let i=0;i<4;i++)x=(x*2+1)%13;return x;}],
  ['reverse-fold', 'return [2,5,1,4].reduceRight((a,x)=>a*2+x,0);', () => [2,5,1,4].reduceRight((a,x)=>a*2+x,0)],
  ['mask', 'return ((45 & 27) << 1) ^ 7;', () => ((45&27)<<1)^7],
  ['nested-count', 'let n=0; for(let i=0;i<5;i++) for(let j=0;j<i;j++) if((i+j)%2===0) n++; return n;', () => {let n=0;for(let i=0;i<5;i++)for(let j=0;j<i;j++)if((i+j)%2===0)n++;return n;}],
  ['mutation', 'let a=[1,2,3,4]; for(let i=1;i<a.length;i++) a[i]+=a[i-1]; return a[3];', () => {let a=[1,2,3,4];for(let i=1;i<a.length;i++)a[i]+=a[i-1];return a[3];}],
  ['popcount', 'let x=173,n=0; while(x){x&=x-1;n++;} return n;', () => {let x=173,n=0;while(x){x&=x-1;n++;}return n;}],
  ['euclid', 'let a=84,b=30; while(b){let t=a%b;a=b;b=t;} return a;', () => {let a=84,b=30;while(b){let t=a%b;a=b;b=t;}return a;}],
  ['alternating', 'let s=0; for(let i=1;i<=7;i++) s+=(i%2 ? i : -i); return s;', () => {let s=0;for(let i=1;i<=7;i++)s+=(i%2?i:-i);return s;}],
  ['recursive-fold', 'let a=1,b=3; for(let i=0;i<4;i++){let t=a+b;a=b;b=t;} return b;', () => {let a=1,b=3;for(let i=0;i<4;i++){let t=a+b;a=b;b=t;}return b;}],
  ['filter-map', 'return [1,2,3,4,5,6].filter(x=>x%3!==0).map(x=>x*x).reduce((a,b)=>a+b,0);', () => [1,2,3,4,5,6].filter(x=>x%3!==0).map(x=>x*x).reduce((a,b)=>a+b,0)],
];
export const tasks = validateTasks(cases.map(([id, code, oracle], i) => {
  const value = oracle();
  const answer = i % 4;
  const choices = [value - 2, value - 1, value + 1].map(String);
  choices.splice(answer, 0, String(value));
  return [id, `What integer does this JavaScript function body return?\n${code}`, choices, answer];
}));
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  console.log(JSON.stringify(tasks));
}
