"""Small parallel graph predictor with deterministic decoding.

Expression templates come from training graphs only. Heads select operators,
templates (including constants/comparisons), and input/prior-output bindings.
No source tokens are generated. This initial finite template bank is a measured
expressiveness limit, not a claim that arbitrary new glue can be predicted.
"""
from __future__ import annotations
import ast

import torch
from torch import nn

from . import call_graph

INPUTS = 8
REFERENCES = 3
PORTS = 4
SLOTS = call_graph.MAX_NODES
OPERATORS = ['EMPTY'] + sorted(call_graph.FUNCTIONS)


def split_expression(source, scope):
    """Separate a bounded expression's syntax from its graph-value bindings."""
    _, _, dependencies = call_graph.expression(source, scope)
    references = []
    class Replace(ast.NodeTransformer):
        def visit_Name(self, node):
            if node.id in dependencies:
                if node.id not in references:
                    references.append(node.id)
                return ast.copy_location(ast.Name(id=f'_value{references.index(node.id)}', ctx=node.ctx), node)
            return node
    tree = Replace().visit(ast.parse(source, mode='eval'))
    if len(references) > REFERENCES:
        raise ValueError('Expression exceeds predictor reference slots')
    return ast.unparse(tree), [scope[name] for name in references]


class Codec:
    def __init__(self, templates):
        self.templates = list(templates)
        self.by_template = {source: i for i, source in enumerate(self.templates)}
        if not self.templates or self.templates[0] != '<PAD>' or len(self.by_template) != len(self.templates):
            raise ValueError('Invalid template vocabulary')

    @classmethod
    def fit(cls, training_pairs):
        templates = set()
        for pair in training_pairs:
            if pair['learning_split'] != 'training':
                raise ValueError('Only training targets can define the expression bank')
            for source, scope in cls.expressions(pair):
                templates.add(split_expression(source, scope)[0])
        return cls(['<PAD>'] + sorted(templates))

    @staticmethod
    def expressions(pair):
        params = [p[0] for p in pair['input']['params']]
        if len(params) > INPUTS:
            raise ValueError('Too many problem inputs')
        scope = {name: i for i, name in enumerate(params)}
        for i, node in enumerate(pair['target']['nodes']):
            for source in node['arguments']:
                yield source, dict(scope)
            scope[node['output']] = INPUTS + i
        yield pair['target']['answer'], scope

    def encode(self, pair):
        components = torch.zeros(SLOTS, dtype=torch.long)
        templates = torch.full((SLOTS + 1, PORTS), -100, dtype=torch.long)
        bindings = torch.full((SLOTS + 1, PORTS, REFERENCES), -100, dtype=torch.long)
        scope = {p[0]: i for i, p in enumerate(pair['input']['params'])}
        if len(scope) > INPUTS:
            raise ValueError('Too many problem inputs')
        def encode_expression(source, slot, port):
            template, refs = split_expression(source, scope)
            if template not in self.by_template:
                raise ValueError('Target needs a template absent from training')
            templates[slot, port] = self.by_template[template]
            for i, ref in enumerate(refs):
                bindings[slot, port, i] = ref
        for i, node in enumerate(pair['target']['nodes']):
            components[i] = OPERATORS.index(node['operator'])
            for j, source in enumerate(node['arguments']):
                encode_expression(source, i, j)
            scope[node['output']] = INPUTS + i
        encode_expression(pair['target']['answer'], SLOTS, 0)
        return components, templates, bindings

    def decode(self, components, templates, bindings, params):
        scope = {i: name for i, name in enumerate(params)}
        def expression(slot, port):
            template = self.templates[int(templates[slot, port])]
            if template == '<PAD>':
                raise ValueError('Missing expression prediction')
            class Bind(ast.NodeTransformer):
                def visit_Name(self, node):
                    if node.id.startswith('_value'):
                        index = int(node.id.removeprefix('_value'))
                        reference = int(bindings[slot, port, index])
                        if reference not in scope:
                            raise ValueError('Predicted unavailable or future binding')
                        return ast.copy_location(ast.Name(id=scope[reference], ctx=node.ctx), node)
                    return node
            return ast.unparse(Bind().visit(ast.parse(template, mode='eval')))
        nodes, ended = [], False
        for i in range(SLOTS):
            operator = OPERATORS[int(components[i])]
            if operator == 'EMPTY':
                ended = True
                continue
            if ended:
                raise ValueError('Nontrailing EMPTY prediction')
            arguments = [expression(i, j) for j in range(call_graph.FUNCTIONS[operator][1])]
            output = f'value_{i}'
            if output in params:
                raise ValueError('Output/input name conflict')
            nodes.append({'operator': operator, 'arguments': arguments, 'output': output})
            scope[INPUTS + i] = output
        return {'schema': call_graph.SCHEMA, 'vocabulary_sha256': call_graph.vocabulary_hash(),
                'nodes': nodes, 'answer': expression(SLOTS, 0)}


class ParallelGraphPredictor(nn.Module):
    def __init__(self, embedding_dim, template_count, width=64):
        super().__init__()
        self.project = nn.Linear(embedding_dim, width)
        self.slots = nn.Parameter(torch.randn(SLOTS + 1, width) * .02)
        layer = nn.TransformerEncoderLayer(width, 4, dim_feedforward=width*2,
                                            dropout=0., batch_first=True)
        self.encoder = nn.TransformerEncoder(layer, 2, enable_nested_tensor=False)
        self.component = nn.Linear(width, len(OPERATORS))
        self.template = nn.Linear(width, PORTS * template_count)
        self.binding = nn.Linear(width, PORTS * REFERENCES * (INPUTS + SLOTS))
        self.template_count = template_count

    def forward(self, query, retrieved_contracts):
        # All slots attend to the query, retrieved contracts, and each other in
        # one forward call. No autoregressive loop or retry is hidden here.
        projected = self.project(query)
        slots = projected[:, None, :] + self.slots[None, :, :]
        memory = self.project(retrieved_contracts)
        state = self.encoder(torch.cat([slots, memory], dim=1))[:, :SLOTS+1]
        batch = state.shape[0]
        return (self.component(state[:, :SLOTS]),
                self.template(state).view(batch, SLOTS+1, PORTS, self.template_count),
                self.binding(state).view(batch, SLOTS+1, PORTS, REFERENCES, INPUTS+SLOTS))


def supervised_loss(predicted, target):
    losses = []
    for logits, labels in zip(predicted, target):
        flat = labels.reshape(-1)
        if (flat != -100).any():
            losses.append(nn.functional.cross_entropy(logits.reshape(-1, logits.shape[-1]), flat))
    return sum(losses)
