"""Conservative Python binding spans for global injective spelling maps."""
import ast
import keyword
import symtable

REFLECTION={'eval','exec','compile','locals','globals','vars','dir','getattr','setattr','delattr','__import__',
            '_getframe','currentframe','__dict__','__code__','__closure__','__globals__','__annotations__','__qualname__'}


def record(text):
    if not text.isascii():return {'names':[],'reserved':[],'unsafe':True}
    tree=ast.parse(text);table=symtable.symtable(text,'candidate.py','exec')
    reserved=set(keyword.kwlist)|{'self','cls'}
    identifiers=set();eligible=set();unsafe=False
    def symbols(t):
        for s in t.get_symbols():
            identifiers.add(s.get_name())
            if t.get_type()!='function' or s.is_global() or s.is_nonlocal() or s.is_free() or s.is_imported() or s.is_namespace():
                reserved.add(s.get_name())
            elif s.is_local():eligible.add(s.get_name())
        for child in t.get_children():symbols(child)
    symbols(table)
    lines=text.splitlines(keepends=True);offsets=[0]
    for line in lines:offsets.append(offsets[-1]+len(line))
    spans={}
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            reserved.add(n.name)
            if n.decorator_list or getattr(n,'type_params',[]):unsafe=True
        if isinstance(n,ast.Attribute):
            identifiers.add(n.attr);reserved.add(n.attr)
            if n.attr in REFLECTION:unsafe=True
        if isinstance(n,ast.Name) and n.id in REFLECTION:unsafe=True
        if isinstance(n,ast.keyword):
            if n.arg is None:unsafe=True
            else:reserved.add(n.arg)
        if isinstance(n,ast.ExceptHandler) and n.name:reserved.add(n.name)
        if isinstance(n,(ast.MatchAs,ast.MatchStar)) and n.name:reserved.add(n.name)
        if isinstance(n,ast.MatchMapping) and n.rest:reserved.add(n.rest)
        name=n.id if isinstance(n,ast.Name) else n.arg if isinstance(n,ast.arg) else None
        if name is not None:
            identifiers.add(name);start=offsets[n.lineno-1]+n.col_offset
            assert text[start:start+len(name)]==name
            spans.setdefault(name,set()).add((start,start+len(name)))
    names=[] if unsafe else [{'name':n,'spans':sorted(spans.get(n,[]))} for n in eligible-reserved if spans.get(n)]
    names.sort(key=lambda r:(-len(r['spans']),r['name']))
    return {'names':names,'reserved':sorted((identifiers|reserved)-{n['name'] for n in names}),'unsafe':unsafe}


def forbidden(text,entry):
    """Exact source and entry method/body strings, with and without first-line indent."""
    tree=ast.parse(text);out={text};lines=text.splitlines(keepends=True)
    offsets=[0]
    for line in lines:offsets.append(offsets[-1]+len(line.encode()))
    for cls in tree.body:
        if isinstance(cls,ast.ClassDef) and cls.name=='Solution':
            for method in cls.body:
                if isinstance(method,(ast.FunctionDef,ast.AsyncFunctionDef)) and method.name==entry:
                    out.add(ast.get_source_segment(text,method))
                    out.add(''.join(lines[method.lineno-1:method.end_lineno]).rstrip('\n'))
                    if method.body:
                        first,last=method.body[0],method.body[-1]
                        chunk=''.join(lines[first.lineno-1:last.end_lineno])
                        out.add(chunk.rstrip('\n'))
                        offset=first.col_offset
                        out.add(chunk.encode()[offset:].decode().rstrip('\n'))
                        out.add(text.encode()[offsets[first.lineno-1]+first.col_offset:offsets[last.end_lineno-1]+last.end_col_offset].decode())
    assert len(out)>1,'entry method not found'
    return {s for s in out if s}
