x=require('fs').readFileSync('/dev/stdin','utf8').trim().split(/\s/);
yobi=new Array("Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday");
for(i=0;i<x.length-1;){
    if(x[i]==0)break;
    console.log(yobi[new Date('2004/0'+x[i++]+'/0'+x[i++]).getDay()]);
}