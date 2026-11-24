class Matrix {
    constructor(w, h, init) {
        this.d = new Array(w);
        for (let i = 0; i < w; ++i) {
            this.d[i] = new Array(h).fill(init);
        }
    }

    get width() {
        return this.d.length;
    }

    get height() {
        if (this.d.length === 0) {
            return 0;
        }
        return this.d[0].length;
    }

    submatrix(x1, x2, y1, y2) {
        const rvalue = new Matrix(x2 - x1, 0, 0);
        for (let i = 0; i < rvalue.width; ++i) {
            rvalue.d[i] = this.d[x1 + i].slice(y1, y2);
        }
        return rvalue;
    }

    flip_h() {
        for (let i = 0, j = this.width - 1; i < j; ++i, --j) {
            [this.d[i], this.d[j]] = [this.d[j], this.d[i]];
        }
        return this;
    }

    flip_v() {
        for (let i = 0, j = this.height - 1; i < j; ++i, --j) {
            for (let k = 0; k < this.width; ++k) {
                [this.d[k][i], this.d[k][j]] = [this.d[k][j], this.d[k][i]];
            }
        }
        return this;
    }

    add(m) {
        const rvalue = new Matrix(Math.max(this.width, m.width), Math.max(this.height, m.height), 0);
        for (let i = 0; i < rvalue.width; ++i) {
            for (let j = 0; j < rvalue.height; ++j) {
                if (i < this.width && j < this.height) {
                    rvalue.d[i][j] += this.d[i][j];
                }
                if (i < m.width && j < m.height) {
                    rvalue.d[i][j] += m.d[i][j];
                }
            }
        }
        return rvalue;
    }
}

new Promise(function(resolve, reject) {
    let cin = "";
    process.stdin
        .on("data", chunk => { cin += chunk; })
        .on("end", () => { resolve([cin, process.stdout]) });
}).then(function([cin, cout]) {
    const sc = cin.split(/[ \n]/).map(elt => parseInt(elt))[Symbol.iterator]();
    for (;;) {
        let n = sc.next().value;
        let m = sc.next().value;
        const t = sc.next().value;
        const p = sc.next().value;
        if (n === 0 && m === 0 && t === 0 && p === 0) break;
        let a = new Matrix(n, m, 1);
        for (let i = 0; i < t; ++i) {
            const d = sc.next().value;
            const c = sc.next().value;
            if (d === 1) {
                a = a.submatrix(0, c, 0, a.height).flip_h().add(a.submatrix(c, a.width, 0, a.height));
            } else {
                a = a.submatrix(0, a.width, 0, c).flip_v().add(a.submatrix(0, a.width, c, a.height));
            }
        }
        for (let i = 0; i < p; ++i) {
            const x = sc.next().value;
            const y = sc.next().value;
            cout.write(`${a.d[x][y]}\n`);
        }
    }
});

