// inputに入力データ全体が入る
function Main(input) {

    input = input.split("\n");
  
    let vals = input[0].split(" ");
    
    let A = parseInt(vals[0], 10);  // 赤
    let B = parseInt(vals[1], 10);  // 緑
    let C = parseInt(vals[2], 10);  // 青

    let cnt = parseInt(input[1], 10);

    let i = 0;

    while (A >= B) {
        B = B * 2;
        i++;
    }

    while (B >= C) {
        C = C * 2;
        i++;
    }

    if (i <= cnt) {
        console.log("Yes");
    } else {
        console.log("No");
    }
}


Main(require("fs").readFileSync("/dev/stdin", "utf8"));