const input = require('fs').readFileSync('/dev/stdin', 'utf8');
const lines = input.trim().split('\n');
 
while (line = lines.shift()) {
    const [n, max] = line.split(' ').map(Number);
    if (n === 0 && max === 0) {break;}
    let prices = lines.shift().split(' ').map(Number);
    let maxPrice = 0;
 
    for (let i = 0; i < n; i++) {
        for (let j = 0; j < n; j++) {
            if (i === j) continue;
 
            var sum = prices[i] + prices[j]; 
            if (sum > max) continue;
            maxPrice = Math.max(maxPrice, sum);
        }
    }
 
    console.log(maxPrice === 0 ? 'NONE': maxPrice);
}
