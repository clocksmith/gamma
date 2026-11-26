function Main(input) {
    // 1行目がinput[0], 2行目がinput[1], …に入る
    tmp = input.split("\n");
    tmp = tmp.map(Number);
    
    N = tmp[0];
    m = Math.min(tmp[1],tmp[2],tmp[3],tmp[4],tmp[5]);
    answer = 4 + Math.ceil(N/m);
    console.log(answer);
    
    
}
//*この行以降は編集しないでください（標準入出力から一度に読み込み、Mainを呼び出します）
Main(require("fs").readFileSync("/dev/stdin", "utf8"));


