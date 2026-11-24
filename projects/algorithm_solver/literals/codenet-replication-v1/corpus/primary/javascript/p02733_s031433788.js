function Main(input) {
    input = input.trim().split("\n").map(function(x) { return x.split(" ")});
    var H = parseInt(input[0][0], 10);
    var W = parseInt(input[0][1], 10);
    var K = parseInt(input[0][2], 10);
    arr_S = [];
    arr_SS = [];
    var tmp;
    for (var i = 0; i < H; i ++){
        arr_S.push(input[i + 1][0].split("").map(e => parseInt(e, 10)));
        arr_SS.push([0]);
        tmp = 0;
        for (var j = 0; j < W; j ++){
            tmp += arr_S[i][j];
            arr_SS[i].push(tmp);
        }
    }
    // console.log(arr_S, arr_SS);
    
    var N = H - 1; //N桁の2進数
    var hDiv;
    var tmpRowSet;
    var tmpSum; 
    var CountHCut;
    var tmpCut;
    var ans = (H - 1) + (W - 1);
    whole_loop:
    for (var k = 0; k < Math.pow(2, N); k++){
    // for (var k = 3; k < 4; k++){        
        hDiv = [0, 1, 2, 3, 4, 5, 6, 7];
        hDiv.length = H;
        tmpRowSet = [arr_SS[0].slice()];
        // console.log(hDiv, H);
        tmp = k.toString(2);
        tmp = ('0'.repeat(N) + tmp).substr(-1*N);
        CountHCut = 0;
        // console.log(arr_SS)
        for (var l = 0; l < tmp.length; l++){
            // console.log("l", l);
            if (tmp.substr(l, 1) === '0'){
                hDiv[l + 1] = hDiv[l];
                tmpRowSet[tmpRowSet.length - 1] = VO(tmpRowSet[tmpRowSet.length - 1], arr_SS[l + 1], '+');
            } else {
                tmpRowSet.push(arr_SS[l + 1].slice());
                CountHCut ++;
            }
        }
        // console.log("hD",hDiv);
        // console.log("tRS", tmpRowSet);
        tmpSum = [0, 0, 0, 0, 0, 0, 0, 0];
        tmpSum.length = tmpRowSet.length;
        tmpCut = [];
        for (var i = 1; i <= W; i++){
            part_loop:
            for (var j = 0; j < tmpRowSet.length; j++){
                // console.log("ji", j, i, tmpRowSet[j][i], tmpSum[j], tmpCut);
                if (tmpRowSet[j][i] - tmpSum[j] > K) {
                    if (i === 1 || tmpCut[tmpCut.length - 1] === i - 1) continue whole_loop;
                    tmpCut.push(i - 1); //i-1列目とi列目の間にカットが入る
                    for (var jj = 0; jj < tmpRowSet.length; jj++){
                        tmpSum[jj] = tmpRowSet[jj][i - 1];
                        // console.log("here");
                    }
                    i --;
                    break part_loop;
                } 
            }
        }
        // console.log(CountHCut, tmpCut.length, tmpCut);
        ans = Math.min(ans, CountHCut + tmpCut.length);
        // console.log("a", ans);

    }
    console.log(ans);
    
}


function VO(v1, v2, op){
    var ans = []
    if (v1.length !== v2.length) {
      if (v2.length == 1){
        v2 = Array.from({ length: (v1.length) }, () => v2);
      } else {
          return null;
      }
    }
    for (var i = 0; i < v1.length; i++){
        if (op == '+') {
            ans.push(v1[i] + v2[i]);
        } 
        if (op == '-') {
            ans.push(v1[i] - v2[i]);
        } 
        if (op == '*') {
            ans.push(v1[i] * v2[i]);
        } 
        if (op == '/') {
            ans.push(v1[i] / v2[i]);
        } 
        if (op == '%') {
            ans.push(v1[i] % v2[i]);
        } 
        if (op == '||') {
            ans.push(Math.max(v1[i],v2[i]));
        } 
    }
    return ans;    
}

Main(require("fs").readFileSync("/dev/stdin", "utf8")); 
