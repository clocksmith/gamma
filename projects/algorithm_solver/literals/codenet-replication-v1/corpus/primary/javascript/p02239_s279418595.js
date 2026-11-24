function Main(input) {
    input = input.trim().split("\n").map(function(x) { return x.split(" ")});
    var n = parseInt(input[0][0], 10);
    var line;
    arr_distance = Array.from({length: n}, () => [0, -1]);
    arr_v = [];
    for (var i = 0; i < n; i++){
        line = input[i + 1].map(e => parseInt(e, 10));
        arr_v.push([]);
        for (var j = 2; j < line.length; j++){
            arr_v[i].push(line[j]);
        }
        arr_distance[i][0] = i + 1;
    }
    distance = 0;
    currentLayer = [1];
    nextLayer = [];
    finished = BFS(currentLayer);

    for (var x of arr_distance){
        console.log(x.join(" "))
    }
}

function BFS(currentLayer){
    while (true){
        for (let x of currentLayer){
            arr_distance[x - 1][1] = distance;
        }
        for (let x of currentLayer){
            for (var y of arr_v[x - 1]){
                if (arr_distance[y - 1][1] === -1) nextLayer.push(y);
            }
        }
        if (nextLayer.length === 0) return true;
        currentLayer = nextLayer.slice();
        nextLayer = [];
        distance ++;
    }
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));
