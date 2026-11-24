"use strict"
function Main(stdin){
let stdout = [];

stdin = stdin.trim().split("\n");
let n = parseInt(stdin[0].split(" ")[0])
let m = parseInt(stdin[0].split(" ")[1])

let ab = [];
for (let i = 0; i < m; i++){
    ab.push(Array.from(stdin[i+1].split(" "), x => parseInt(x)))
}

let s1 = new Set();
for (let i = 0; i < m; i++){
    if (ab[i][0] === 1){ s1.add(ab[i][1]) }
}

let s2 = new Set();
for (let i = 0; i < m; i++){
    if (ab[i][1] === n){ s2.add(ab[i][0]) }
}

function intersection(setA, setB) {
    var _intersection = new Set();
    for (var elem of setB) {
        if (setA.has(elem)) {
            _intersection.add(elem);
        }
    }
    return _intersection;
}

if (intersection(s1,s2).size > 0){
    stdout.push("POSSIBLE")
}else{
    stdout.push("IMPOSSIBLE")
}


console.log(stdout.join("\n"));
return stdout
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"))