//catoonさんを参考に実装

function main(input) {
  const n = parseInt(input[0]);

  //素因数分解してmapにぶち込む
  const map = {};
  let k = n;
  for(let i = 2; i*i <= k; i++){
    if(k % i === 0){
      map[i] = 0;
      while(k % i === 0){
        map[i]++;
        k /= i;
      }
    }
  }

  //N自体が素数の場合は上で引っかからないのでここで処理
  if(k > 1){
    map[k] = 1;
  }

  //素数の値ではなく数のみを配列に入れる
  const primeCnt = [];
  for(let i in map){
    primeCnt.push(map[i])
  };

  //同じ素数でも複数に分けれる場合がある
  let cnt = 0;
  for(let i = 0; i < primeCnt.length; i++){
    for(let j = 1; j <= primeCnt[i]; j++){
      cnt++;
      primeCnt[i] -= j;
    }
  }
  console.log(cnt);
}

main(require('fs').readFileSync('/dev/stdin', 'utf8').trim().split("\n"));