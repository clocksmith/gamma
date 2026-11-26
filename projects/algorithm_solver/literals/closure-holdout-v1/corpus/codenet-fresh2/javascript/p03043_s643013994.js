'use strict'

function Main(input){
    let temp = input.trim().split(' ').map((v)=>parseInt(v));
    let n = temp.shift();
    let k = temp.shift();

    let ans = 0;
    for(let i=1;i<=n;i++){
        let j=i;
        let m=0;
        while(j < k){
            j <<= 1;
            m++;
        }
        ans += (1/n)*(1/(1<<m));
    }

    console.log(ans);

}
//*この行以降は編集しないでください（標準入出力から一度に読み込み、Mainを呼び出します）
Main(require("fs").readFileSync("/dev/stdin", "utf8"));
