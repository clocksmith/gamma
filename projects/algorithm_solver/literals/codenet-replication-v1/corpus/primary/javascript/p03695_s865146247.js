function color(rate) {
    if (1 <= rate && rate <= 399) return "gray";
    if (400 <= rate && rate <= 799) return "brown";
    if (800 <= rate && rate <= 1199) return "green";
    if (1200 <= rate && rate <= 1599) return "light_blue";
    if (1600 <= rate && rate <= 1999) return "blue";
    if (2000 <= rate && rate <= 2399) return "yellow";
    if (2400 <= rate && rate <= 2799) return "orange";
    if (2800 <= rate && rate <= 3199) return "red";
    return "free";
}
function Main(input) {
    input = input.split("\n");
    var a = input[1].split(" ");
    var col = {};
    var ans = 0;
    for (var i of a) {
        if (!col[color(i)]) {
            col[color(i)] = 1;
            if (color(i) != "free") ans++;
        }
        else col[color(i)]++;
    }
    if (ans == 0) console.log(1 + " " + col.free);
    else console.log(ans + " " + (ans + (col.free ? col.free : 0)));
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));