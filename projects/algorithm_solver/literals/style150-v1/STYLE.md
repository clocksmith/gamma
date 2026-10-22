# Shared style v1 for literal rewrites

Every rewrite of a development program follows these rules, so the same exact text
recurs across problems and a 256-entry literal vocabulary can cover it in large pieces.
A rewrite keeps the original's algorithm and its asymptotic time and memory. It must match
the original's observed behavior on every corpus case: result, result type, arguments
after the call, and alias edges.

## Shape

1. The program is one line (plus a kept constructor line, rule 3) with no comments and no
   trailing newline. Whitespace appears
   only where JavaScript needs it: `let x`, `return x`, `of a`, `new M`, `typeof x`,
   `else if`, `in`, `instanceof`.
2. Entry: `function solve(a,b,c){...}`, parameters `a`, `b`, `c`, `d`, `e` in order.
   Helper functions are declared before `solve` as `function F(...){...}`, then `G`, `H`.
   An arrow function is used only as an argument (sort comparators, `Array.from`
   initializers, callbacks).
3. If the original ends with a charged constructor line (`class ListNode ...` or
   `class TreeNode ...`), keep that line byte for byte, after `solve` on its own line. Build
   nodes with `new ListNode(...)` or `new TreeNode(...)`.

## Declarations and names

4. `let` only, one variable per statement: `let x=...;`. No `const`, no `var`, no
   destructuring declarations except `let [x,y]=...;` when unpacking a pair.
5. Names come from roles, never from the original:

   | Name | Role |
   | --- | --- |
   | `n`, `m` | `let n=a.length;`, then `let m=b.length;` or `let m=a[0].length;` |
   | `i`, `j`, `k` | loop indices, outer to inner |
   | `r` | the value `solve` returns |
   | `x`, `y` | element values in `for...of`, comparator and callback parameters |
   | `s` | running sum or current string |
   | `c` | counts array |
   | `d` | DP or distance table |
   | `q` | queue or stack array |
   | `l`, `h`, `t` | low, high, midpoint |
   | `p` | pointer, previous value or node |
   | `u`, `v`, `g` | graph nodes and adjacency list |
   | `M`, `S` | a `Map`, a `Set` |
   | `e`, `o`, `w`, `z` | further locals, in that order |

   Inside a helper, parameters are `a`, `b`, `c` in order, and locals follow the same table.
   Never shadow a name in an enclosing scope.

## Statements

6. Bodies always have braces: `if(...){...}`, `}else{`, `}else if(...){`. Use a
   conditional expression only inside an expression.
7. `===` and `!==`; `i++`, `i--`, `r++`; compound `r+=x;`. Never `+=1`.
8. Loops use exactly these heads:
   - `for(let i=0;i<n;i++){` (another start: `let i=1`; another bound: `i<m`, `i<=n`)
   - `for(let i=n-1;i>=0;i--){`
   - `for(let x of a){`
   - `while(q.length>0){`, `while(l<h){`
9. Preferred exact forms when the algorithm needs them:

   | Need | Text |
   | --- | --- |
   | result start | `let r=0;` `let r=[];` `let r=1;` `let r=-1;` `let r=Infinity;` |
   | collections | `let M=new Map();` `let S=new Set();` `let q=[];` |
   | 1-D table | `let d=new Array(n+1).fill(0);` |
   | 2-D table | `let d=Array.from({length:n},()=>new Array(m).fill(0));` |
   | count in map | `M.set(x,(M.get(x)\|\|0)+1);` |
   | count lowercase | `let c=new Array(26).fill(0);for(let x of a){c[x.charCodeAt(0)-97]++;}` |
   | sorted copy | `let b=[...a].sort((x,y)=>x-y);` |
   | best so far | `r=Math.max(r,...);` `r=Math.min(r,...);` |
   | binary search | `let l=0;let h=n;while(l<h){let t=(l+h)>>1;if(...){l=t+1;}else{h=t;}}` |
   | finish | `return r;}` |

10. Use `n` (or `m`) instead of `a.length` once it is defined. Put declarations at the
    top of their block in the order they are first used.
11. Remove checks that only reject inputs outside the problem's stated constraints, and
    code that cannot run. Keep every check that affects a valid input. Keep mutation and
    aliasing exactly as the original does: if the original returns a new array, so does the
    rewrite; if it mutates an argument, so does the rewrite.

When two phrasings are equivalent, choose the one this page lists. When this page does not
cover a case, choose the shortest phrasing already used elsewhere in your rewrites.
