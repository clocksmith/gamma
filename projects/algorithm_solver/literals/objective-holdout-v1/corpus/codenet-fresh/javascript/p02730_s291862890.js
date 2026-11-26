process.stdin.resume();
process.stdin.setEncoding('utf8');

function kaibun(s){
    l = s.length;
    var flag = true;
    for (var i=0; i<(l-l%2)/2; i++){
        if (s[i] != s[l-1-i]){
            flag = false;
        }
    }

    return flag;
}

function Main(input){
    var s = input.trim();
    var mae = s.substr(0, (s.length-1)/2);
    var ato = s.substr(((s.length+3)/2)-1, (s.length-1)/2);
    var ans = kaibun(s) && kaibun(mae) && kaibun(ato);
    if (ans){
        console.log("Yes");
    } else{
        console.log("No");
    }
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));