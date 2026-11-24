"use strict";

class Dice {
    /**
     *    +--+
     *    |0 |
     * +--+--+--+--+
     * |3 |1 |2 |4 |
     * +--+--+--+--+
     *    |5 |
     *    +--+
     */
    constructor(stat) {
        this.stat = stat.slice(0, 6);
    }

    fix(top, front) {
        switch (this.stat.indexOf(top)) {
            case 1: this.rot_ns(1); break;
            case 2: this.rot_we(1); break;
            case 3: this.rot_we(-1); break;
            case 4: this.rot_ns(-1); break;
            case 5: this.rot_ns(2); break;
        }
        for (let i = 0; i < 4; ++i) {
            if (this.stat[1] === front)
                return true;
            this.rot(1);
        }
        return false;
    }

    rot(val) {
        if (val < 0) val += 4 * Math.floor(-val / 4) + 4;
        const old_i = [1, 2, 4, 3];
        const new_i = [val, val + 1, val + 2, val + 3].map(elt => old_i[elt % 4]);
        [this.stat[old_i[0]], this.stat[old_i[1]], this.stat[old_i[2]], this.stat[old_i[3]]] =
            [this.stat[new_i[0]], this.stat[new_i[1]], this.stat[new_i[2]], this.stat[new_i[3]]];
    }

    rot_ns(val) {
        if (val < 0) val += 4 * Math.floor(-val / 4) + 4;
        const old_i = [0, 1, 5, 4];
        const new_i = [val, val + 1, val + 2, val + 3].map(elt => old_i[elt % 4]);
        [this.stat[old_i[0]], this.stat[old_i[1]], this.stat[old_i[2]], this.stat[old_i[3]]] =
            [this.stat[new_i[0]], this.stat[new_i[1]], this.stat[new_i[2]], this.stat[new_i[3]]];
    }

    rot_we(val) {
        if (val < 0) val += 4 * Math.floor(-val / 4) + 4;
        const old_i = [0, 2, 5, 3];
        const new_i = [val, val + 1, val + 2, val + 3].map(elt => old_i[elt % 4]);
        [this.stat[old_i[0]], this.stat[old_i[1]], this.stat[old_i[2]], this.stat[old_i[3]]] =
            [this.stat[new_i[0]], this.stat[new_i[1]], this.stat[new_i[2]], this.stat[new_i[3]]];
    }

    equals(dice) {
        const cmp = (u, v) => u.map((e, i) => e === v[i]).reduce((car, cdr) => car && cdr, true);
        const self = new Dice(this.stat);
        for (let i = 0; i < 4; ++i) {
            if (cmp(self.stat, dice.stat)) return true;
            self.rot_ns(1);
            for (let j = 0; j < 4; ++j) {
                if (cmp(self.stat, dice.stat)) return true;
                self.rot(1);
            }
            self.rot_ns(-1);
            self.rot(1);
        }
        self.rot_ns(2);
        for (let j = 0; j < 4; ++j) {
            if (cmp(self.stat, dice.stat)) return true;
            self.rot(1);
        }
        return false;
    }
}


new Promise(function (resolve, reject) {
    let content = "";
    process.stdin.on("data", chunk => { content += chunk; });
    process.stdin.on("end", () => { resolve([content, process.stdout]); });
}).then(function([cin, cout]) {
    const [[n], ...data] = cin.split("\n").map(elt => elt.split(" ").map(e => parseInt(e)));
    const dices = data.slice(0, n).map(elt => new Dice(elt));
    for (let i = 0; i < n; ++i) {
        for (let j = i + 1; j < n; ++j) {
            if (dices[i].equals(dices[j])) {
                cout.write("No\n");
                return;
            }
        }
    }
    cout.write("Yes\n");
});

