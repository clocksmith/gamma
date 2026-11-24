function howMuch(items, item, s) {
  try{
  var
  recipe, price = items[item].price,
  sum, flag = false, j;
  s = s || [];
//  console.log(item, s);
  if(recipe = items[item].recipe) {
    s.push(item);
    sum = 0; flag  = true;
    for(j = 0; j < recipe.length; j++) {
      if(s.indexOf(recipe[j]) !== -1 || !(recipe[j] in items)) {
        flag = false;
        break;
      }
      sum += howMuch(items, recipe[j], s);
    }
    if(flag) {
      price = min(price, sum);
    }
    s.pop();
  }
  }catch(e){throw [e,items,item];}
  
  return price;
}

function min(x, y) {
  return x < y ? x : y;
}

function main() {
  var
  i, n, m, line,
  len = input.length,
  items;
  for(i = 0; i < len;) {
    items = {};
    n = parseInt(input[i++], 10) + i;
    if(n === i) break;
    for(; i < n; i++) {
      line = input[i].split(' ');
      items[line[0]] = {price: parseInt(line[1], 10)};
    }
    m = parseInt(input[i++], 10) + i;
    for(; i < m; i++) {
      line = input[i].split(' ');
      items[line[0]].recipe = line.slice(2);
    }
//    console.log(items);
    console.log(howMuch(items, input[i++]));
  }
}

var
input = '';

process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data', function(chunk) {
  input += chunk;
});
process.stdin.on('end', function() {
  input = input.split('\n');
  main();
});