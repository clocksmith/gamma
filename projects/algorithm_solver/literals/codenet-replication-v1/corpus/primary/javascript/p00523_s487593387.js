/// <reference path="node.d.ts" />
/// <reference path="lib.ts" />
function main(input) {
    var n = +input.shift();
    var a = [];
    for (var i = 0; i < n; ++i)
        a.push(+input.shift());
    var s = 0;
    var b = [0];
    for (var i = 0; i < n * 2; ++i) {
        s += a[i % n];
        b.push(s);
    }
    var x = 0, y = 0, z = 0;
    function part(i) {
        if (i === 0)
            return b[y] - b[x];
        if (i === 1)
            return b[z] - b[y];
        return b[x + n] - b[z];
    }
    var ans = 0;
    while (x < n) {
        while (1) {
            ++y;
            var w = z;
            while (part(0) > part(1) && part(2) >= part(0))
                ++z;
            if (part(2) < part(0)) {
                --y;
                z = w;
                break;
            }
        }
        ans = Math.max(part(0), ans);
        ++x;
    }
    console.log(ans);
}
/// <reference path="node.d.ts" />
/// <reference path="main.ts" />
(function () {
    process.stdin.resume();
    process.stdin.setEncoding('utf8');
    var input = '';
    process.stdin.on('data', function (chunk) {
        input += chunk;
    });
    process.stdin.on('end', function (chunk) {
        main(input.split(/\s+/));
    });
})();
// based on lodash
var _;
(function (_) {
    function floor(v) {
        return Math.floor(v);
    }
    _.floor = floor;
    function min(a) {
        return Math.min.apply(Math, a);
    }
    _.min = min;
    function max(a) {
        return Math.max.apply(Math, a);
    }
    _.max = max;
    function reduce(a, func, init) {
        var result = init;
        for (var i = 0; i < a.length; ++i)
            result = func(result, a[i]);
        return result;
    }
    _.reduce = reduce;
    function sortedIndex(a, v) {
        var s = 0, t = a.length;
        while (s < t) {
            var m = _.floor((s + t) / 2);
            if (a[m] < v)
                s = m + 1;
            else
                t = m;
        }
        return s;
    }
    _.sortedIndex = sortedIndex;
    function sum(a) {
        return reduce(a, function (result, v) { return result + v; }, 0);
    }
    _.sum = sum;
})(_ || (_ = {}));