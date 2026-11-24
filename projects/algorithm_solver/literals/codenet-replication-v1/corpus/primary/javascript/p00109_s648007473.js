var
input = '';

process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data', function(chunk) {
    input += chunk;
});
process.stdin.on('end', function() {
    input = input.split('\n');
    main();
});

function main() {
    var
    i,
    n = +input[0],
    lines = input.slice(1);
    for(i = 0; i < n; i++) {
        console.log(calc(lines[i]));
    }
}

function calc(src) {
    src = src.replace(/([-+*\/()=])/g, ' $1 ').split(' ').filter(function(s) {
        return s.trim() !== '';
    });
    return add(src);

    function add(src) {
        var
        ret = mul(src);
        while(src[0] in {'+': 1,'-': 1}) {
            switch(src.shift()) {
            case '+':
                ret += mul(src);
                break;
            case '-':
                ret -= mul(src);
                break;
            }
        }
        return ret;
    }

    function mul(src) {
        var
        val, sign,
        ret = prim(src);
        while(src[0] in {'*': 1,'/': 1}) {
            switch(src.shift()) {
            case '*':
                ret *= prim(src);
                break;
            case '/':
                val = prim(src);
                sign = ret * val < 0 ? -1 : 1;
                ret = sign * Math.floor(Math.abs(ret) / Math.abs(val));
                break;
            }
        }
        return ret;
    }

    function prim(src) {
        var
        ret, 
        head = src.shift();
        switch(head) {
        case '+':
           return prim(src);
        case '-':
           return -prim(src);
        case '(':
           ret = add(src);
           src.shift();
           return ret;
        default:
           return parseInt(head, 10);
        }
    }
}