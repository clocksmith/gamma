class Spreadsheet {
    constructor(rows) {
        this.rows = rows;
        this.cells = new Map();
    }
    setCell(cell, value) { this.cells.set(cell, value); }
    resetCell(cell) { this.cells.delete(cell); }
    getValue(formula) {
        return formula.slice(1).split('+').reduce((total, operand) => {
            const isCell = operand[0] >= 'A' && operand[0] <= 'Z';
            return total + (isCell ? (this.cells.get(operand) || 0) : Number(operand));
        }, 0);
    }
}

function solve(operations, argumentsList) {
    let sheet;
    return operations.map((operation, i) => {
        if (operation === 'Spreadsheet') {
            sheet = new Spreadsheet(...argumentsList[i]);
            return null;
        }
        return sheet[operation](...argumentsList[i]) ?? null;
    });
}
module.exports = {solve, Spreadsheet};
