function Main(input) {
    input = input.split("\n")
    input = input.map(e=>e.split(" "))
    input = input.map(e=>e.map(f=>parseInt(f,10)))

    var a = input[0][0]-input[0][1]*2
    a = a<0 ? 0 : a;
    console.log(a);
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));