"""273. Integer to English Words."""
LESS_THAN_TWENTY = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
                    'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
                    'Seventeen', 'Eighteen', 'Nineteen']
TENS = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
THOUSANDS = ['', 'Thousand', 'Million', 'Billion']

def chunk(value: int) -> str:
    parts = []
    if value >= 100:
        parts.extend((LESS_THAN_TWENTY[value // 100], 'Hundred'))
        value %= 100
    if value >= 20:
        parts.append(TENS[value // 10])
        value %= 10
    if value:
        parts.append(LESS_THAN_TWENTY[value])
    return ' '.join(parts)

def solve(num: int) -> str:
    if num == 0:
        return 'Zero'
    parts = []
    group = 0
    while num:
        num, value = divmod(num, 1000)
        if value:
            text = chunk(value)
            if THOUSANDS[group]:
                text += ' ' + THOUSANDS[group]
            parts.append(text)
        group += 1
    return ' '.join(reversed(parts))

class Solution:
    def numberToWords(self, num: int) -> str:
        return solve(num)
