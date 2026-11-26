var input = '';
process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data', function(chunk) {
    input += chunk;
});
process.stdin.on('end', function() {
    main(input)
});

function main(input){
    var args = input.trim().split('\n');

    var i = 0;
    while(true) {
        var islandCount = parseInt(args[i++]);
        if(isEndInput(islandCount)) break;

        var islands = {};
        for(var j = 1; j <= islandCount; j += 1){
            islands[j] = {};
        }

        var sum = 0;
        for(var j = 0; j < islandCount - 1; j += 1){
            var bridgeData = splitNum(args[i++]);
            var a = bridgeData[0], b = bridgeData[1], cost = bridgeData[2];
            islands[a][b] = islands[b][a] = cost;
            sum += cost;
        }

        var cost = calcCost('1', null, islands);

        var res = (sum - cost.leafCost) * 2 - cost.maxCost;

        console.log(res);

    }
}

function calcCost(current, parent, islands){

    var island = islands[current];

    var isLeaf = true;
    var maxCost = 0;
    var leafCost = 0;
    for(var next in island){
        if(next === parent){ continue; }

        isLeaf = false;
        var childCost = calcCost(next, current, islands);
        leafCost += childCost.leafCost;
        var cost = island[next] + childCost.maxCost;

        if(cost > maxCost){
            maxCost = cost;
        }
    }

    if(isLeaf){
        leafCost += island[parent];
        maxCost -= island[parent];
    }
    return { maxCost : maxCost, leafCost : leafCost };
}

function splitNum(str){
    return str.split(' ').map(Number);
}

function isEndInput(arg){
    return arg === 0;
}