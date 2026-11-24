

process.stdin.resume();
process.stdin.setEncoding('utf8');


process.stdin.on('data', function (chunk) {
    let n = chunk.toString() // 文字列化する
        .split("\n") // \nで分割
        .map(x => Number(x));
        // .filter(x => x !== );
    for (let i = 0; i < n.length; i++) {
        if (n[i] <= 40) {
            n[i] = 40;
        }
    }

    const ans = (n[0] + n[1] + n[2] + n[3] + n[4]) / 5;
    console.log(ans);



})
