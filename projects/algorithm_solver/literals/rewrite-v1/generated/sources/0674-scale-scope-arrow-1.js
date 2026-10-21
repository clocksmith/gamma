const solve=a=>{let b=1;let c=1;for(let d=1;d<a.length;d+=1){if(a[d-1]<a[d]){b+=1;if(b>c){c=b;}}else{b=1;}}return c;};
