var shortestPalindrome=function(s){const reversed=s.split('').reverse().join(''),text=s+'#'+reversed,prefix=Array(text.length).fill(0);for(let i=1;i<text.length;i++){let j=prefix[i-1];while(j&&text[i]!==text[j])j=prefix[j-1];if(text[i]===text[j])j++;prefix[i]=j;}return s.slice(prefix[prefix.length-1]).split('').reverse().join('')+s;};
module.exports={shortestPalindrome};
