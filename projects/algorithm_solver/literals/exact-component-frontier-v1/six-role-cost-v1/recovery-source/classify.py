"""Lossless, conservative JS lexical attribution; NEVER evaluates source.

Not a JS parser: after regex/division ambiguity or templates, contextual labels
remain unresolved through EOF. Exact codepoint-shape attribution always remains.
"""
import collections,re
KEYWORDS=set('break case catch class const continue debugger default delete do else export extends finally for function if import in instanceof let new return super switch this throw try typeof var void while with yield enum implements interface package private protected public static await async of get set true false null undefined'.split())
NUMBER=re.compile(r'(?:0[xX][0-9a-fA-F_]+n?|0[bB][01_]+n?|0[oO][0-7_]+n?|(?:[0-9][0-9_]*(?:\.[0-9_]*)?|\.[0-9][0-9_]*)(?:[eE][+-]?[0-9_]+)?n?)')
def shape(c):
 if c.isspace():return 'whitespace'
 if c in '{}[](),;:.':return 'structural_punctuation'
 if c in '+-*/%=!<>&|^~?':return 'operator_like'
 if c in "'\"`":return 'quote'
 if c.isdecimal():return 'digit'
 if c.isalpha() or c in '_$':return 'identifier_like'
 return 'other'
def lexical(source):
 labels=[None]*len(source);i=0;previous=None
 def fill(a,b,label):labels[a:b]=[label]*(b-a)
 while i<len(source):
  start=i;c=source[i]
  if c.isspace():
   while i<len(source) and source[i].isspace():i+=1
   fill(start,i,'whitespace');continue
  if source.startswith('//',i):
   end=source.find('\n',i);i=len(source) if end<0 else end;fill(start,i,'line_comment');continue
  if source.startswith('/*',i):
   end=source.find('*/',i+2);i=len(source) if end<0 else end+2;fill(start,i,'block_comment');continue
  if c in "'\"":
   quote=c;labels[i]='string_delimiter';i+=1
   while i<len(source):
    if source[i]=='\\':fill(i,min(i+2,len(source)),'string_escape');i+=min(2,len(source)-i)
    elif source[i]==quote:labels[i]='string_delimiter';i+=1;break
    else:labels[i]='string_content';i+=1
   previous='literal';continue
  if c in '`/\\' or (ord(c)>127 and not c.isspace()):
   # Escaped identifiers, Unicode identifier boundaries and regex/template grammar
   # need a real JS tokenizer. Do not falsely report context after ambiguity.
   fill(i,len(source),'unresolved_lexical_context');break
  if c.isalpha() or c in '_$':
   i+=1
   while i<len(source) and (source[i].isascii() and (source[i].isalnum() or source[i] in '_$')):i+=1
   token=source[start:i]
   role='member_name_after_dot' if previous=='.' else 'keyword_or_contextual_word' if token in KEYWORDS else 'binding_candidate_after_declaration' if previous in ('let','const','var','function','class') else 'identifier_other'
   fill(start,i,role);previous=token;continue
  match=NUMBER.match(source,i)
  if match:
   i=match.end();fill(start,i,'numeric_literal');previous='literal';continue
  labels[i]='punctuator_or_operator';previous=c;i+=1
 assert len(labels)==len(source) and all(x is not None for x in labels)
 return labels

def summarize(vocabulary,selected,variants):
 lexical_counts=collections.Counter();shape_counts=collections.Counter();cross=collections.Counter();per_problem=[]
 total=0
 for pid,(key,path) in sorted(selected.items()):
  source=variants[pid][key];labels=lexical(source);at=0;local=collections.Counter()
  for literal_id in path[2]:
   literal=vocabulary[literal_id]
   if source[at:at+len(literal)]!=literal:raise ValueError('path position mismatch')
   if len(literal)==1:
    category=labels[at];form=shape(literal);lexical_counts[category]+=1;shape_counts[form]+=1;cross[(category,form)]+=1;local[category]+=1;total+=1
   at+=len(literal)
  if at!=len(source) or sum(local.values())!=path[1]:raise ValueError('complete source/singleton accounting mismatch')
  per_problem.append({'problem_id':pid,'singleton_count':path[1],'lexical_counts':dict(sorted(local.items()))})
 return {'singleton_count':total,'lexical_counts':dict(sorted(lexical_counts.items())),'codepoint_shape_counts':dict(sorted(shape_counts.items())),'cross_counts':[{'lexical_role':a,'codepoint_shape':b,'count':n}for (a,b),n in sorted(cross.items())],'per_problem':per_problem,'classification_scope':'Exact partition of shortest-path singleton positions. Conservative lexical scanner, NOT full JS semantic roles; ambiguity suffix explicitly unresolved. Codepoint shapes exact. No lexemes/literals/source bytes published.'}
