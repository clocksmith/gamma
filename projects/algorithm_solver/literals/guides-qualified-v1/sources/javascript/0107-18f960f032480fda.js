var implementation = function (p0) {
    const v0 = [];
    if (!p0) {
        return v0;
    }
    const v1 = [p0];
    while (v1.length) {
        const v2 = [];
        const v3 = [];
        for (const {
                    val: v4,
                    left: v5,
                    right: v6
                } of v1) {
            v2.push(v4);
            v5 && v3.push(v5);
            v6 && v3.push(v6);
        }
        v0.push(v2);
        v1.splice(0, v1.length, ...v3);
    }
    return v0.reverse();
};
function solve(p0) {
    return implementation(p0);
}
