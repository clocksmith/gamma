function main(input) {
    var n, m, tmp, a, b, c, g, dist, i, j, k, inf, t, negativeLoop;
    inf = -100000000000000;

    tmp = input[0].split(" ");
    n = parseInt(tmp[0]);
    m = parseInt(tmp[1]);

    g = [];
    dist = [];
    for (i = 0; i < n; i++) {
        g.push([]);
        dist.push(inf)
    }
    dist[0] = 0;

    for (i = 0; i < m; i++) {
        tmp = input[1 + i].split(" ");
        a = parseInt(tmp[0]) - 1;
        b = parseInt(tmp[1]) - 1;
        c = parseInt(tmp[2]);
        g[a].push([b, c]);
    }

    for (k = 0; k < n; k++) {
        for (i = 0; i < n - 1; i++) {
            if (dist[i] === inf) {
                continue;
            }
            for (j = 0; j < g[i].length; j++) {
                t = g[i][j][0];
                c = g[i][j][1];
                if (dist[t] < dist[i] + c) {
                    dist[t] = dist[i] + c;
                }
            }
        }
    }

    negativeLoop = false;
    for (k = 0; k < n; k++) {
        for (i = 0; i < n; i++) {
            if (dist[i] === inf) {
                continue;
            }
            for (j = 0; j < g[i].length; j++) {
                t = g[i][j][0];
                c = g[i][j][1];
                if (dist[t] < dist[i] + c) {
                    dist[t] = dist[i] + c;
                    if (t === n - 1) {
                        negativeLoop = true;
                        break;
                    }
                }
            }
            if (negativeLoop) {
                break;
            }
        }
    }

    if (negativeLoop) {
        console.log("inf");
    } else {
        console.log(dist[n - 1]);
    }
}

main(require("fs").readFileSync("/dev/stdin", "utf8").split("\n"));