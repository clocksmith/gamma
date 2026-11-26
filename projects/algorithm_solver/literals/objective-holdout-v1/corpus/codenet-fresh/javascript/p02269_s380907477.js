const line = require('fs').readFileSync('/dev/stdin', 'utf-8').split('\n');

const insert = (map, str) => {
    map[str] = true;
    return map;
};

const find = (map, str) => str in map;

line.slice(1, line.length-1).reduce((acc, x) => {
    const cmd = x.split(' ');
    switch(cmd[0]) {
        case 'insert':
            acc = insert(acc, cmd[1]);
            break;
        case 'find':
            console.log(find(acc, cmd[1]) ? 'yes' : 'no');
            break;
    }

    return acc;
}, {});

