"use strict";
function Main(input) {
    let cin = new Inputer(input);
    let K = cin.getInt();
    const S = (n) => n.toString().split('').reduce((ac, v) => ac + (v - 0), 0);
    const compare = (x, y) => !(x * S(y) <= y * S(x));

    let n = 0, a = 1;
    for (let i = 0; i < K; i++) {
        if (compare(n + a, n + 10 * a)) a *= 10;
        n += a;
        console.log(n);
    }
}
class Inputer{constructor(t){if(typeof t=='undefined')throw new Error('引数（stdin）を省略できません！');this.cnt=0;this.items=t.split(/\n|\s/)}getInt(){return this.items[this.cnt++]-0}getIntArray(t){if(typeof t=='undefined')throw new Error('引数（1以上）を省略できません！');if(t<1)throw new Error('引数は1以上であること！');let r=new Array(t);for(let e=0;e<t;e++)r[e]=this.getInt();return r}getStr(){return this.items[this.cnt++]}getStrArray(t){if(typeof t=='undefined')throw new Error('引数（1以上）を省略できません！');if(t<1)throw new Error('引数は1以上であること！');let r=new Array(t);for(let e=0;e<t;e++)r[e]=this.getStr();return r}}
if (typeof window == "undefined") Main(require("fs").readFileSync("/dev/stdin", "utf8"));