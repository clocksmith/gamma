function Main(input) {
    var idata = input.split(/\s/);
    var a = parseInt(idata[0]);
    var b = parseInt(idata[1]);
    var c = parseInt(idata[2]);
    var nokori = Math.max(0, a - b);
    var ans = Math.max(0, c - nokori);
    console.log(ans);
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));
