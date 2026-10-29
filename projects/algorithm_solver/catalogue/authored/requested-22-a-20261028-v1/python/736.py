"""Original frontend 736 variant; qualification unknown."""

def solve(expression):
    tokens = expression.replace('(', '( ').replace(')', ' )').split()
    bindings = {}
    frames = []
    result = None
    position = 0
    while position < len(tokens):
        token = tokens[position]
        position += 1
        if token == '(':
            frames.append({'op': tokens[position], 'values': [], 'name': None, 'bound': [], 'body': None})
            position += 1
            continue
        frame = frames[-1] if frames else None
        if token == ')':
            frame = frames.pop()
            if frame['op'] == 'add':
                value = frame['values'][0] + frame['values'][1]
            elif frame['op'] == 'mult':
                value = frame['values'][0] * frame['values'][1]
            else:
                value = frame['body']
                for name in frame['bound']:
                    bindings[name].pop()
        elif (frame is not None and frame['op'] == 'let' and frame['name'] is None and
              token[0].isalpha() and tokens[position] != ')'):
            frame['name'] = token
            continue
        elif token[0].isalpha():
            value = bindings[token][-1]
        else:
            value = int(token)
        if not frames:
            result = value
            continue
        parent = frames[-1]
        if parent['op'] != 'let':
            parent['values'].append(value)
        elif parent['name'] is not None:
            bindings.setdefault(parent['name'], []).append(value)
            parent['bound'].append(parent['name'])
            parent['name'] = None
        else:
            parent['body'] = value
    return result


class Solution:
    def evaluate(self, expression):
        return solve(expression)
