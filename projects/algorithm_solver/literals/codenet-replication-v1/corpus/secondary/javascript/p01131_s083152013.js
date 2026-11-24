process.stdin.resume();
process.stdin.setEncoding("utf8");
process.stdin.on("data", function (chunk) {
    var input = chunk.trim().split("\n");
    var n = input.shift();
    var button = ["", ".,!? ", "abc", "def", "ghi", "jkl", "mno", "pqrs", "tuv", "wxyz"];
    button = button.map(function (key) {
        return key.split("");
    });
    for (var i = 0; i < n; i++) {
        var data = input[i].split("").map(Number);
        var message = "";
        var character = "";
        var count = 0;
        data.forEach(function (key) {
            if (key > 0) {
                character = button[key][count % button[key].length];
                count++;
            } else {
                message += character;
                character = "";
                count = 0;
            }
        });
        console.log(message);
    }
});