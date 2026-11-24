function isValid(input, i, j) {
    var dx = [-1, 0, 1, 0];
    var dy = [0, -1, 0, 1];
    var k;
    for (k = 0; k < 4; k++) {
        var xx = i + dx[k];
        var yy = j + dy[k]; 
        if (xx < 0 || yy < 0 || xx >= input.length || yy >= input[i].length) continue;
        if (input[xx][yy] === '#') {
            return true;
        }
    }
    return false;
}

function Main(inp) {
    var input = inp.split('\n').slice(1).map(function(line) {
        return line.split('');
    });
    var i, j;
    for (i = 0; i < input.length; i++) {
        for (j = 0; j < input[i].length; j++) {
            var v = input[i][j];
            if (v !== '#') continue; // # だけ
            if (!isValid(input, i, j)) {
                console.log('No');
                return;
            }
        }
    }
    console.log('Yes');
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));