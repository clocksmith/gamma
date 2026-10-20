// Parse/print/check only. Candidate source is never evaluated here.
const fs = require('node:fs');
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const generate = require('@babel/generator').default;
const request = JSON.parse(fs.readFileSync(0, 'utf8'));
try {
  const tree = parser.parse(request.source, {sourceType:'script'});
  const formatted = generate(tree, {comments:true, compact:false, concise:false}).code + '\n';
  const errors = [], bindings = {}, helpers = {}, captures = [];
  if (tree.program.body.some(node=>!['FunctionDeclaration','ClassDeclaration'].includes(node.type))) errors.push('module body supports only unconditional function and adapter declarations');
  const policy = request.policy;
  const protectedNames = new Set(['Solution']);
  let adapter = null;
  const seen = new Set();
  traverse(tree, {
    Class(path) {
      if (!path.isClassDeclaration() || !path.parentPath.isProgram() || path.node.id?.name !== 'Solution' || path.node.superClass || path.node.decorators?.length || path.node.body.body.length !== 1) errors.push('only a top-level plain Solution adapter class is supported');
    },
    Function(path) {
      if (path.node.async || path.node.generator) errors.push('async/generator callable is unsupported');
      if (path.isFunctionExpression()) errors.push('function expressions require reviewed extension');
      if (path.isObjectMethod()) errors.push('object methods require reviewed extension');
      if (path.isArrowFunctionExpression()) {
        // The sole anonymous callback profile constructs a fresh empty bucket.
        const parent = path.parentPath.node;
        if (path.node.params.length || path.node.body.type !== 'ArrayExpression' || path.node.body.elements.length || parent.type !== 'CallExpression' || parent.callee.type !== 'MemberExpression' || parent.callee.computed || parent.callee.object.name !== 'Array' || parent.callee.property.name !== 'from' || parent.arguments[1] !== path.node) errors.push('unsupported arrow callable');
      }
    },
    ClassMethod(path) {
      const node = path.node;
      if (path.parentPath.parentPath.node.id?.name === 'Solution' && node.key.name === request.entry.method) {
        if (adapter) errors.push('duplicate public adapter');
        adapter = node;
        if (node.kind !== 'method' || node.async || node.generator || node.static || node.computed) errors.push('unsupported public method');
        if (JSON.stringify(node.params.map(p=>p.name)) !== JSON.stringify(request.entry.params)) errors.push('public signature mismatch');
        const body=node.body.body, call=body[0]?.argument;
        if (body.length!==1 || body[0].type!=='ReturnStatement' || call?.type!=='CallExpression' || call.callee.name!==request.entry.internal || JSON.stringify(call.arguments.map(p=>p.name))!==JSON.stringify(request.entry.params)) errors.push('adapter must forward exact positional arguments once');
        const binding = path.scope.getBinding(request.entry.internal);
        if (!binding?.path.isFunctionDeclaration() || !binding.path.parentPath.isProgram() || !policy.helpers[request.entry.internal]) errors.push('adapter internal must resolve to a registered module function');
      } else errors.push('unregistered class method');
    },
    FunctionDeclaration(path) {
      const node=path.node;helpers[node.id.name]=node.params.map(p=>p.name);
      const spec=policy.helpers[node.id.name];
      if (!spec || JSON.stringify(spec.params)!==JSON.stringify(helpers[node.id.name])) errors.push('helper signature mismatch: '+node.id.name);
    },
    CallExpression(path) {
      if (path.node.callee.type==='Identifier') {
        const spec=policy.helpers[path.node.callee.name];
        if (spec && (path.node.arguments.some(arg=>arg.type==='SpreadElement') || path.node.arguments.length!==spec.params.length)) errors.push('helper arity mismatch: '+path.node.callee.name);
        if (['eval','Function'].includes(path.node.callee.name)) errors.push('dynamic evaluation not supported');
      }
    },
    ReferencedIdentifier(path) {
      if (path.node.name === 'Solution') errors.push('adapter class cannot be referenced or mutated by candidate code');
      if (!path.scope.getBinding(path.node.name) && !['Array','Math','ListNode'].includes(path.node.name)) errors.push('unsupported unresolved reference: '+path.node.name);
    },
    'AssignmentExpression|UpdateExpression|UnaryExpression'(path) {
      if (path.isUnaryExpression() && path.node.operator !== 'delete') return;
      let root = path.node.left || path.node.argument;
      const propertyWrite = root?.type === 'MemberExpression';
      while (root?.type === 'MemberExpression') root = root.object;
      if (propertyWrite && policy.helpers[root?.name]) errors.push('helper properties cannot be mutated');
    },
    'IfStatement|ForStatement|ForOfStatement|WhileStatement'(path) {
      for (const node of [path.node.body,path.node.consequent,path.node.alternate]) if (node && !['BlockStatement','IfStatement'].includes(node.type)) errors.push('control body requires multiline block');
    },
    Scopable(path) {
      for (const binding of Object.values(path.scope.bindings)) {
        if (seen.has(binding)) continue;seen.add(binding);
        const name=binding.identifier.name;
        if ((protectedNames.has(name) || binding.path.isFunctionDeclaration()) && binding.constantViolations.length) errors.push('protected callable binding reassigned: '+name);
        if (protectedNames.has(name) && binding.path.isClassDeclaration() && binding.path.parentPath.isProgram()) continue;
        const fn=binding.scope.getFunctionParent()?.path;
        if (binding.kind==='param' && fn?.isClassMethod() && fn.node.key.name===request.entry.method) continue;
        const key=`${binding.identifier.loc.start.line}:${binding.identifier.loc.start.column}:${name}`;
        const ancestor=binding.scope.parent?.getBinding(name);
        if (ancestor && ancestor!==binding) errors.push('live binding shadowing: '+key);
        const role=Object.keys(policy.roles).find(role=>policy.roles[role]===name);
        bindings[key]={name,role:role||null,references:binding.referencePaths.length};
        for (const ref of binding.referencePaths) if (ref.scope.getFunctionParent()!==binding.scope.getFunctionParent()) captures.push({binding:key,reference_line:ref.node.loc.start.line});
      }
    }
  });
  if (!adapter) errors.push('missing exact Solution method adapter');
  if (request.mapping) {
    const mapping=request.mapping;
    if (mapping.schema!=='algsolve.reviewed-bindings.v1' || !mapping.reviewed_by) errors.push('reviewed binding mapping required');
    const hash=require('node:crypto').createHash('sha256').update(request.source).digest('hex');
    if (mapping.source_sha256!==hash) errors.push('stale reviewed mapping');
    for (const [key,binding] of Object.entries(bindings)) {
      const role=mapping.bindings[key];
      if (!role || !policy.roles[role] || policy.roles[role]!==binding.name) errors.push('unreviewed or noncanonical binding: '+key);
    }
    for (const key of Object.keys(mapping.bindings)) if (!bindings[key]) errors.push('stale binding: '+key);
    if (request.source!==formatted) errors.push('noncanonical formatting');
  }
  process.stdout.write(JSON.stringify({formatted,bindings,helpers,captures,errors}));
} catch (error) {
  process.stdout.write(JSON.stringify({errors:['parse/check failure: '+error.message]}));
  process.exitCode=1;
}
