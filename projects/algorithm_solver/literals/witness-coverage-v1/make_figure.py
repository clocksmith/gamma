#!/usr/bin/env python3
"""Draw the witness-rule coverage figure from the frozen inputs. Needs matplotlib.

Exact budgets are a solid line. Elsewhere the band runs from the best verified dictionary (lower edge) to
the proven ceiling (upper edge). The single-character curve is drawn separately, so the gap between it and
the lower edge is what witnessed multi-character entries add.

    python3 -B make_figure.py [coverage.json] [OUT_STEM]
"""
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'coverage.json')))
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'witness-coverage')
rows = {r['slots']: r for r in data['rows']}
ks = sorted(rows)

BLUE, ORANGE = '#2a78d6', '#eb6834'                      # validated pair: categorical slots 1 and 2
INK, INK2, MUTED, GRID, AXIS, SURFACE = '#0b0b0b', '#52514e', '#898781', '#e1e0d9', '#c3c2b7', '#ffffff'
plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['Helvetica Neue', 'Helvetica', 'Arial', 'DejaVu Sans'],
                     'font.size': 9, 'pdf.fonttype': 42})
fig, ax = plt.subplots(figsize=(7.0, 4.4), facecolor=SURFACE)
ax.set_facecolor(SURFACE)


def runs(test):
    out, run = [], []
    for k in ks:
        if test(rows[k]):
            run.append(k)
        elif run:
            out.append(run)
            run = []
    if run:
        out.append(run)
    return out


# Unresolved budgets: a wash from the verified dictionary to the proven ceiling, joined to its exact neighbours.
for run in runs(lambda r: not r['exact']):
    xs = [k for k in [run[0] - 1] + run + [run[-1] + 1] if k in rows]
    lower, upper = [rows[k]['lower'] for k in xs], [rows[k]['upper'] for k in xs]
    ax.fill_between(xs, lower, upper, color=BLUE, alpha=0.12, linewidth=0, zorder=1)
    ax.plot(xs, upper, color=MUTED, linewidth=1.1, solid_capstyle='round', zorder=2)
    ax.plot(xs, lower, color=BLUE, linewidth=1.1, solid_capstyle='round', zorder=3)

ax.plot(ks, [rows[k]['singleCharacters'] for k in ks], color=ORANGE, linewidth=2, solid_capstyle='round', solid_joinstyle='round', zorder=4)

for run in runs(lambda r: r['exact']):
    if len(run) > 1:
        ax.plot(run, [rows[k]['lower'] for k in run], color=BLUE, linewidth=2.4, solid_capstyle='round', solid_joinstyle='round', zorder=5)


def dot(k, y):
    ax.plot([k], [y], marker='o', markersize=6.5, color=BLUE, markeredgecolor=SURFACE, markeredgewidth=1.6, linestyle='none', zorder=7)


def label(k, y, text, dx, dy, ha):
    ax.annotate(text, xy=(k, y), xytext=(k + dx, y + dy), ha=ha, va='center', color=INK, fontsize=8.5,
                arrowprops=dict(arrowstyle='-', color=AXIS, linewidth=0.8, shrinkA=2, shrinkB=4), zorder=8)


# Two interval labels and two exact anchors.
for k, dx, dy in ((16, -1.5, 22), (32, -1.5, 22)):
    r = rows[k]
    ax.plot([k, k], [r['lower'], r['upper']], color=INK2, linewidth=0.9, zorder=6)
    for y in (r['lower'], r['upper']):
        ax.plot([k - 0.7, k + 0.7], [y, y], color=INK2, linewidth=0.9, zorder=6)
    label(k, r['upper'], f"{k} slots: {r['lower']} to {r['upper']}", dx, dy, 'center')
dot(64, rows[64]['lower'])
label(64, rows[64]['lower'], f"64 slots: exactly {rows[64]['lower']},\nunder both rules", -11, 13, 'right')
dot(ks[-1], rows[ks[-1]]['lower'])
label(ks[-1], rows[ks[-1]]['lower'], f"All 80 need {ks[-1]} slots", -5, -22, 'right')

ax.set_xlim(0, ks[-1] + 2)
ax.set_ylim(0, 84)
ax.set_xticks([0, 16, 32, 48, 64, 80, ks[-1]])
ax.set_yticks([0, 20, 40, 60, 80])
ax.set_xlabel('Dictionary slots', color=INK2)
ax.set_ylabel('Programs spelled exactly, of 80', color=INK2)
ax.grid(axis='y', color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
for side in ('top', 'right', 'left'):
    ax.spines[side].set_visible(False)
ax.spines['bottom'].set_color(AXIS)
ax.spines['bottom'].set_linewidth(0.8)
ax.tick_params(axis='both', length=0, labelsize=8.5)
for tick in ax.get_xticklabels() + ax.get_yticklabels():
    tick.set_color(INK2)

handles = [Line2D([], [], color=BLUE, linewidth=2.4, label='Witness rule, exact'),
           Line2D([], [], color=MUTED, linewidth=1.1, label='Witness rule, proven ceiling'),
           Line2D([], [], color=BLUE, linewidth=1.1, label='Witness rule, best verified dictionary'),
           Line2D([], [], color=ORANGE, linewidth=2, label='Single characters only, exact')]
ax.legend(handles=handles, loc='lower right', bbox_to_anchor=(1.0, 0.03), frameon=False, fontsize=8.5, handlelength=1.8,
          borderaxespad=0.2, labelcolor=INK)
fig.tight_layout()
fig.savefig(out + '.pdf', facecolor=SURFACE)
fig.savefig(out + '.png', dpi=200, facecolor=SURFACE)

with open(out + '.csv', 'w') as f:
    f.write('slots,witness_lower,witness_upper,witness_exact,upper_source,single_characters,unrestricted_maximum\n')
    for k in ks:
        r = rows[k]
        f.write(f"{k},{r['lower']},{r['upper']},{'yes' if r['exact'] else 'no'},\"{r['upperSource']}\",{r['singleCharacters']},{r['unrestrictedMaximum']}\n")
print('wrote', os.path.basename(out) + '.pdf, .png, .csv')
