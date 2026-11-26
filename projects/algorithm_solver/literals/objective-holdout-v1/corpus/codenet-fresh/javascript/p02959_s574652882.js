var kills = 0

function main(arg) {
    var N = parseInt( arg.split(/\n/)[0] );
    var A = arg.split(/\n/)[1].split(/\s/).map( str => parseInt(str, 10) );
    var B = arg.split(/\n/)[2].split(/\s/).map( str => parseInt(str, 10) );
    var kill = 0;
    for(i=0;i<N;i++){
        //1つめの町で敵を倒す
        fight(i,i,A,B);
        //2つめの町で敵を倒す
        fight(i,i+1,A,B);
    }
    console.log(kills);
}

function fight(myid,town,A,B){
    if(A[town]>=B[myid]){
        A[town]-=B[myid];
        kills += B[myid];
        B[myid]=0;
    }else if(A[town]<B[myid]){
        B[myid]-=A[town];
        kills += A[town];
        A[town]=0;
    }
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'));