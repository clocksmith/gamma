function solve(s){const words=s.split(' ');function count(word){let total=0;for(const c of word)if('aeiou'.includes(c))total++;return total;}const target=count(words[0]);for(let i=1;i<words.length;i++)if(count(words[i])===target)words[i]=words[i].split('').reverse().join('');return words.join(' ');}

var reverseWords = solve;
module.exports = solve;
