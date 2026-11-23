#!/usr/bin/env python3
"""Figures of the fixed-source paper, from source-free summaries only.

    make_figures.py <summary.json> <bounds.json> <chains.json> <output folder>
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

INK, MUTED, GRID = '#0b0b0b', '#52514e', '#e4e3df'
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET = ('#2a78d6', '#eb6834', '#1baf7a', '#eda100',
                                                     '#e87ba4', '#008300', '#6250d6')
SEQUENCE = ['#b7d3f2', '#86b6ea', '#5a98e0', '#2a78d6', '#1c5aa6', '#123c70']
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8, 'axes.edgecolor': MUTED,
                     'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.linewidth': .6,
                     'xtick.major.width': .6, 'ytick.major.width': .6, 'pdf.fonttype': 42,
                     'axes.titlesize': 9, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left'})
TICKS = [64, 256, 1024, 4096]
TITLES = {'python': 'Python (400 files)', 'javascript': 'JavaScript (400 files)',
          'both': 'Both languages (800 files)'}


def size_axis(axis):
    axis.set_xscale('log', base=2)
    axis.set_xticks(TICKS)
    axis.set_xticklabels([str(t) for t in TICKS])
    axis.minorticks_off()
    axis.set_xlim(64, 4096)
    axis.grid(True, axis='y', color=GRID, lw=.6)
    axis.set_axisbelow(True)


def thousands(axis):
    axis.yaxis.set_major_formatter(lambda value, _: f'{value / 1000:.0f}k')


def series(summary, corpus, limit, arm, field='emissions'):
    points = []
    for cell in summary['table']:
        if cell['corpus'] == corpus and cell['L'] == limit and cell['B'] is None and arm in cell['arms']:
            value = cell['arms'][arm].get(field)
            if value is not None:
                points.append((cell['K'], value))
    return sorted(points)


def best_series(summary, corpus, limit, arms, cap=None):
    points = []
    for cell in summary['table']:
        if cell['corpus'] == corpus and cell['L'] == limit and cell['B'] == cap:
            values = [cell['arms'][a]['emissions'] for a in arms
                      if a in cell['arms'] and cell['arms'][a]['emissions'] is not None]
            if values:
                points.append((cell['K'], min(values)))
    return sorted(points)


def emissions_figure(summary, bounds, out):
    figure, axes = plt.subplots(1, 3, figsize=(7.2, 2.75), sharey=False)
    for axis, corpus in zip(axes, ('python', 'javascript', 'both')):
        alphabet = summary['limits']['corpora'][corpus]['alphabet']
        total = summary['limits']['corpora'][corpus]['bytes']
        axis.axvspan(64, alphabet, color='#f1f0ec', lw=0)
        axis.axhline(total, color=MUTED, lw=1, ls=(0, (4, 2)))
        for arms, color, label, style in (
            (('freq-occ', 'freq-doc'), YELLOW, 'Best frequency', '-'),
            (('bpe',), ORANGE, 'BPE, shortest parse', '-'),
            (('greedy-entry', 'greedy-byte', 'greedy-polish'), BLUE, 'Greedy, best found', '-'),
        ):
            xs, ys = zip(*best_series(summary, corpus, 16, arms))
            axis.plot(xs, ys, color=color, lw=1.7, ls=style, marker='o', ms=2.4, label=label)
        ordinary = series(summary, corpus, 16, 'bpe', 'ordinary')
        if ordinary:
            xs, ys = zip(*ordinary)
            axis.plot(xs, ys, color=ORANGE, lw=.9, ls=(0, (2, 1.5)), label='BPE, its own segmentation')
        proved = sorted((b['K'], b['lower_bound']) for b in bounds if b['corpus'] == corpus and b['L'] == 16)
        if proved:
            xs, ys = zip(*proved)
            axis.plot(xs, ys, ls='none', marker='^', ms=4.2, mfc='white', mec=VIOLET, mew=1, label='Certified lower bound')
        size_axis(axis)
        thousands(axis)
        axis.set_ylim(0, total * 1.08)
        axis.set_title(TITLES[corpus])
        axis.set_xlabel('Entries in the dictionary')
        axis.text(66, total * .03, 'too few:\nproved\nimpossible', color=MUTED, fontsize=6.3, va='bottom')
        axis.text(4000, total * 1.012, 'single characters', color=MUTED, fontsize=6.3, ha='right', va='bottom')
    axes[0].set_ylabel('Total tokens to spell every file')
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc='lower center', ncol=5, frameon=False, fontsize=7, handlelength=2.2,
                  columnspacing=1.2)
    figure.tight_layout(rect=(0, .085, 1, 1), w_pad=.8)
    figure.savefig(out / 'fig-v3-emissions.pdf')
    plt.close(figure)


def length_figure(summary, chains, out):
    figure, axes = plt.subplots(1, 2, figsize=(7.2, 2.75))
    lengths = (2, 4, 8, 16, 32, 64)
    for limit, color in zip(lengths, SEQUENCE):
        rows = [r for r in chains[f'both-L{limit}-greedy-entry'] if r[2] >= 0]
        axes[0].plot([r[0] for r in rows], [r[2] for r in rows], color=color, lw=1.5)
        if limit <= 8:
            axes[0].text(4150, rows[-1][2], f'{limit}', color=INK, fontsize=6.6, va='center')
        rows_b = [r for r in chains[f'both-L{limit}-greedy-byte'] if r[2] >= 0]
        axes[1].plot([r[1] / 1024 for r in rows_b], [r[2] for r in rows_b], color=color, lw=1.5,
                     label=f'up to {limit} bytes')
    size_axis(axes[0])
    axes[0].set_xlim(94, 4096)
    axes[0].set_xticks([128, 256, 512, 1024, 2048, 4096])
    axes[0].set_xticklabels(['128', '256', '512', '1024', '2048', '4096'])
    axes[0].text(4150, 34000, '16+', color=INK, fontsize=6.6, va='center')
    thousands(axes[0])
    axes[0].set_ylim(0, None)
    axes[0].set_title('Fewer tokens as the list grows')
    axes[0].set_xlabel('Entries in the dictionary')
    axes[0].set_ylabel('Total tokens, both languages')
    axes[1].set_xscale('log', base=2)
    axes[1].set_xticks([.25, 1, 2, 4, 8, 16, 32, 64])
    axes[1].set_xticklabels(['¼', '1', '2', '4', '8', '16', '32', '64'])
    axes[1].minorticks_off()
    axes[1].set_xlim(.18, 64)
    axes[1].grid(True, axis='y', color=GRID, lw=.6)
    axes[1].set_axisbelow(True)
    for budget in (1, 2, 4, 8, 16, 32, 64):
        axes[1].axvline(budget, color=GRID, lw=.6, zorder=0)
    thousands(axes[1])
    axes[1].set_ylim(0, None)
    axes[1].set_title('The same trade-off, paid in stored bytes')
    axes[1].set_xlabel('Stored dictionary (KiB); lines mark frozen budgets')
    axes[1].legend(frameon=False, fontsize=6.6, ncol=2, title='Longest entry', title_fontsize=6.8, loc='upper right')
    figure.tight_layout(w_pad=1.6)
    figure.savefig(out / 'fig-v3-length-storage.pdf')
    plt.close(figure)


def sharing_figure(summary, out):
    figure, axes = plt.subplots(1, 2, figsize=(7.2, 2.5), gridspec_kw={'width_ratios': [1.25, 1]})
    axis = axes[0]
    for limit, color, label in ((4, YELLOW, 'up to 4 bytes'), (16, BLUE, 'up to 16 bytes'), (64, VIOLET, 'up to 64 bytes')):
        points = [(r['K'], 100 * (r['separate'] - r['shared']) / r['shared']) for r in summary['sharing']
                  if r['L'] == limit and r['B'] is None and r['shared'] and r['separate']]
        points.sort()
        axis.plot(*zip(*points), color=color, lw=1.6, marker='o', ms=2.6, label=label)
    axis.axhline(0, color=INK, lw=.8)
    axis.axvspan(64, 183, color='#f1f0ec', lw=0)
    axis.text(67, 30, 'both\nalphabets\ndo not fit', color=MUTED, fontsize=6.3, va='center')
    size_axis(axis)
    axis.set_title('What sharing buys')
    axis.set_xlabel('Combined entries')
    axis.set_ylabel('Extra tokens, two lists (%)')
    axis.legend(frameon=False, fontsize=6.8, loc='upper right')
    axis = axes[1]
    profile = summary['profile']['by_budget']
    labels, both, py, js = [], [], [], []
    for budget in (256, 1024):
        used = profile[f'both-K{budget}']['saved_by_user']
        total = sum(used.values())
        labels.append(f'{budget} entries')
        both.append(100 * used['both'] / total)
        py.append(100 * used['python_only'] / total)
        js.append(100 * used['javascript_only'] / total)
    positions = [1, 0]
    axis.barh(positions, both, color=BLUE, height=.55, label='used by both languages', edgecolor='white', linewidth=1)
    axis.barh(positions, py, left=both, color=ORANGE, height=.55, label='Python only', edgecolor='white', linewidth=1)
    axis.barh(positions, js, left=[a + b for a, b in zip(both, py)], color=AQUA, height=.55, label='JavaScript only',
              edgecolor='white', linewidth=1)
    for y, a, b, c in zip(positions, both, py, js):
        for left, width in ((0, a), (a, b), (a + b, c)):
            if width >= 7:
                axis.text(left + width / 2, y, f'{width:.0f}%', ha='center', va='center', color='white', fontsize=7)
    axis.set_yticks(positions)
    axis.set_yticklabels(labels, color=INK)
    axis.set_xlim(0, 100)
    axis.set_xlabel('Share of tokens saved by the shared dictionary')
    axis.set_title('Who uses the shared entries')
    axis.legend(frameon=False, fontsize=6.6, loc='upper center', bbox_to_anchor=(.5, -.28), ncol=3, handlelength=1.1,
                columnspacing=.9)
    figure.tight_layout(w_pad=1.4)
    figure.savefig(out / 'fig-v3-sharing.pdf')
    plt.close(figure)


def kinds_figure(summary, out):
    groups = (('crosses a boundary', ('crosses a boundary',), BLUE),
              ('identifier', ('identifier',), ORANGE),
              ('keyword', ('keyword',), AQUA),
              ('punctuation', ('punctuation',), YELLOW),
              ('whitespace', ('indentation', 'space', 'newline'), MAGENTA),
              ('constant', ('number', 'string'), GREEN),
              ('comment', ('comment',), VIOLET))
    keys = [('python', 256), ('javascript', 256), ('both', 256), ('python', 1024), ('javascript', 1024), ('both', 1024)]
    names = {'python': 'Python', 'javascript': 'JavaScript', 'both': 'Both'}
    figure, axis = plt.subplots(figsize=(7.2, 2.5))
    positions = [6.4, 5.6, 4.8, 3.2, 2.4, 1.6]
    left = [0.0] * len(keys)
    profile = summary['profile']['by_budget']
    for name, members, color in groups:
        widths = []
        for corpus, budget in keys:
            row = profile[f'{corpus}-K{budget}']
            widths.append(100 * sum(row['saved_by_kind'].get(m, 0) for m in members) / row['saved_total'])
        axis.barh(positions, widths, left=left, color=color, height=.62, label=name, edgecolor='white', linewidth=.9)
        for y, start, width in zip(positions, left, widths):
            if width >= 6:
                axis.text(start + width / 2, y, f'{width:.0f}', ha='center', va='center', fontsize=6.8,
                          color='white' if color not in (YELLOW, MAGENTA) else INK)
        left = [a + b for a, b in zip(left, widths)]
    axis.set_yticks(positions)
    axis.set_yticklabels([names[c] for c, _ in keys], color=INK)
    axis.text(-20, 5.6, '256\nentries', va='center', ha='center', color=MUTED, fontsize=7)
    axis.text(-20, 2.4, '1024\nentries', va='center', ha='center', color=MUTED, fontsize=7)
    axis.set_xlim(0, 100)
    axis.set_xlabel('Share of the tokens saved over single characters (%)')
    axis.spines['left'].set_visible(False)
    axis.tick_params(axis='y', length=0)
    axis.legend(frameon=False, ncol=7, loc='lower center', bbox_to_anchor=(.46, 1.0), fontsize=6.7, handlelength=1,
                columnspacing=.9)
    figure.tight_layout()
    figure.subplots_adjust(left=.2)
    figure.savefig(out / 'fig-v3-kinds.pdf')
    plt.close(figure)


def main():
    summary = json.loads(Path(sys.argv[1]).read_text())
    bounds = json.loads(Path(sys.argv[2]).read_text())
    chains = json.loads(Path(sys.argv[3]).read_text())
    out = Path(sys.argv[4])
    out.mkdir(parents=True, exist_ok=True)
    emissions_figure(summary, bounds, out)
    length_figure(summary, chains, out)
    sharing_figure(summary, out)
    kinds_figure(summary, out)


if __name__ == '__main__':
    main()
