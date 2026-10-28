"use strict";
function solve(password) {
let total=0;for(const char of new Set(password)){if(char>='a'&&char<='z')total++;else if(char>='A'&&char<='Z')total+=2;else if(char>='0'&&char<='9')total+=3;else total+=5;}return total;
}
function passwordStrength(password) { return solve(password); }
module.exports=solve;
module.exports.passwordStrength=passwordStrength;
