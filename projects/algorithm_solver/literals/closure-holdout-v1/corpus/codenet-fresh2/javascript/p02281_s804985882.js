function main(_stdin) {
    const stdin = _stdin.trim().split('\n');
    const n = Number(stdin.shift());
    const T = [];
    for (let i = 0; i < n; i++) {
        T[i] = {parent: null, left: null, right: null};
    }
    for (let i = 0; i < n; i++) {
        const [id, left, right] = stdin[i].split(' ').map(Number);
        T[id].left = left;
        T[id].right = right;
        if(left > -1) {
            T[left].parent = id;
        }
        if(right > -1) {
            T[right].parent = id;
        }
    }

    const rootid = getRootId(T);

    console.log('Preorder');
    const preids = [];
    preorder(rootid, T, preids);
    console.log('', preids.join(' '));

    console.log('Inorder');
    const inids = [];
    inorder(rootid, T, inids);
    console.log('', inids.join(' '));

    console.log('Postorder');
    const postids = [];
    postorder(rootid, T, postids);
    console.log('', postids.join(' '));
}

function getRootId(T) {
    for (let i = 0, l = T.length; i < l; i++) {
        if(T[i].parent === null) return i;
    }
}

function preorder(id, T, ids) {
    if(id === -1) {
        return;
    }
    ids.push(id);
    preorder(T[id].left, T, ids);
    preorder(T[id].right, T, ids);
}

function inorder(id, T, ids) {
    if(id === -1) {
        return;
    }
    inorder(T[id].left, T, ids);
    ids.push(id);
    inorder(T[id].right, T, ids);
}


function postorder(id, T, ids) {
    if(id === -1) {
        return;
    }
    postorder(T[id].left, T, ids);
    postorder(T[id].right, T, ids);
    ids.push(id);
}


main(require('fs').readFileSync('/dev/stdin', 'utf8'));

