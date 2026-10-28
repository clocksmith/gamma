
var isNumber = function(s) {
let i=0,digits=0;const n=s.length;if(i<n&&(s[i]==='+'||s[i]==='-'))i++;while(i<n&&s[i]>='0'&&s[i]<='9'){digits++;i++;}if(i<n&&s[i]==='.'){i++;while(i<n&&s[i]>='0'&&s[i]<='9'){digits++;i++;}}if(digits===0)return false;if(i<n&&(s[i]==='e'||s[i]==='E')){i++;if(i<n&&(s[i]==='+'||s[i]==='-'))i++;const start=i;while(i<n&&s[i]>='0'&&s[i]<='9')i++;if(i===start)return false;}return i===n;
};
module.exports = {isNumber};
