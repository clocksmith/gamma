function main(input) {
    var moneys = [300000,200000,100000];
    var inputs = input.split(' ');
    var codeRank = parseInt(inputs[0],10);
    var machineRank = parseInt(inputs[1],10);
    var ret = 0;
    if(codeRank <= 3)
        ret += moneys[codeRank -1];
    if(machineRank <= 3)
        ret += moneys[machineRank -1];
    if((codeRank == 1) && (machineRank == 1))
        ret += 400000;
    console.log(ret);
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'));