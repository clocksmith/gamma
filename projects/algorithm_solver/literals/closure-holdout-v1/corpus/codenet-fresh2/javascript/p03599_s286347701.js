function Main(input){

  var inp = input.split(' ');
  var A = parseInt(inp[0]); // 水の量
  var B = parseInt(inp[1]); // 水の量
  var C = parseInt(inp[2]); // 砂糖の量
  var D = parseInt(inp[3]); // 砂糖の量
  var E = parseInt(inp[4]); // 水100gあたりの溶ける砂糖の量
  var F = parseInt(inp[5]); // 砂糖水の総量
  
  var waterTotal = []; // とりうる水の量
  var sugarTotal = []; // とりうる砂糖の量
  
  var sugarWater = []; // とりうる砂糖水の量
  var sugarWeight = []; // とりうる砂糖の量
  
  // とりうる水と砂糖の量を列挙
  for(var i = 0; i <= F; i++){
    for(var j = 0; j <= F; j++){
      var water = ((A * i) + (B * j)) * 100; // 水の量
      if(water <= F ) waterTotal.push(water); 
  
      var sugar = (C * i + D * j); // 砂糖の量
      if(sugar <= F) sugarTotal.push(sugar);
    }
  }  
  
  // とりうる砂糖水と砂糖の量を列挙
  for(var i = 0; i <= F; i++){
    for(var j = 0; j <= F; j++){
      var sw = waterTotal[i] + sugarTotal[j]; // 砂糖水の量
      var meltSugar = 100 * sugarTotal[j] / waterTotal[i]; // 水に溶ける砂糖の量
      if( sw <= F && meltSugar <= E){
        sugarWater.push(sw); 
        sugarWeight.push(sugarTotal[j]);
      }
    }
  }
  
  // 各砂糖水と砂糖の量から、濃度を求める
  var noudo = 0;
  var noudoIndex = 0;
  for(var i = 0; i < sugarWater.length; i++){
    var noudoTmp = (100 * sugarWeight[i]) / sugarWater[i]; // 砂糖水の濃度
    if(noudoTmp > noudo){
      noudo = noudoTmp;
      noudoIndex = i;
    }
  }
  
  console.log(sugarWater[noudoIndex] + ' ' + sugarWeight[noudoIndex]);
}
Main(require('fs').readFileSync('/dev/stdin', 'utf8'));