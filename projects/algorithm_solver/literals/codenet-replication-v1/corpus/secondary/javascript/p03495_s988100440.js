function Main(input) {
    const lines = input.split(/\n/);
    const limit = parseInt(lines[0].split(/\s/)[1], 10);
    var changeNums = 0;
    var numList = {};
    lines[1].split(/\s/).forEach(num => {
        if (numList[num]) {
            numList[num] = numList[num] + 1;
        } else {
            numList[num] = 1;
        }
    });
    Object.keys(numList).sort((a,b) =>{
        if (numList[a] > numList[b]) return -1;
        if (numList[a] < numList[b]) return 1;
        return 0;
    }).slice(limit).forEach(key=>{
        changeNums += numList[key];
    });
    console.log(changeNums);
}
Main(require('fs').readFileSync('/dev/stdin', 'utf8'));