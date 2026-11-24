const Main = () => {
    // const line = '2119';
    const lines = require('fs').readFileSync('/dev/stdin', 'utf8');
    const line = lines.split('\n')[0];
    const mod = {};
    for (let i = 1; i < 2019; i ++) {
        mod[i] = -1;
    }
    mod[0] = 0;
    let count = 0;
    for (let i = line.length - 1, m = 0, k = 1; 0 <= i; i--) {
        const n = parseInt(line[i], 10);
        m = ((n * k) + m) % 2019;
        k = (k * 10) % 2019;
        // console.log(m);
        mod[m] ++;
        count += mod[m];
    }
    console.log(count);
}

Main();