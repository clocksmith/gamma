class Solution:
    def numberToWords(self, num):
        if num == 0:
            return 'Zero'
        small = ('', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen')
        tens = ('', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety')
        def words(value):
            if value == 0:
                return []
            if value < 20:
                return [small[value]]
            if value < 100:
                return [tens[value // 10]] + words(value % 10)
            if value < 1000:
                return [small[value // 100], 'Hundred'] + words(value % 100)
            for scale, name in ((1000000000, 'Billion'), (1000000, 'Million'), (1000, 'Thousand')):
                if value >= scale:
                    return words(value // scale) + [name] + words(value % scale)
        return ' '.join(words(num))
