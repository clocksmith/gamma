"use strict";
    
const main = arg => {
    arg = arg.trim().split("\n");
    const K = parseInt(arg[0].split(" ")[0]);
    
    // lunlun数の集合を受け取り、次の桁のlunlun数の州法を返す
    const calcNext = (lunluns) => {
        let result = [];
        
        for(let val of lunluns) {
            for(let j=-1; j<=1; j++) {
                let add = (val % 10) + j;
                if(add >= 0 && add <= 9) {
                    result.push(val * 10 + add)
                }
            }
        }
 
        return result;
    }
    
    let all = []; // 全列挙したもの
    let current = []; 
    
    // 1桁のとき
    for(let v=1; v<10; v++) {
        current.push(v);
        all.push(v);
    }
    
    // 10桁のlunlun数まで出す
    for(let d=1; d<10; d++) {
        current = calcNext(current);
        
        for(let val of current) {
            all.push(val);
        }
    }
    
    // console.log("all:" + all);
    // console.log("cur:" + current);
    
    console.log(all[K-1]);
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));
