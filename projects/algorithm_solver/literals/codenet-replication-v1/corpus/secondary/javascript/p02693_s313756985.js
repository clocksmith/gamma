function Main(input) {
    let k = input.split('\n')[0];
    let a = input.split('\n')[1].split(' ')[0];
    let b = input.split('\n')[1].split(' ')[1];

    let result = 'NG';

    for (let i = 1; k * i <= 1000; i++) {
        if (a <= (k * i) && (k * i) <= b) {
            result = 'OK';
            break;
        }
    }
    console.log(result);
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));