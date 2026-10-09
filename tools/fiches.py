#!/usr/bin/env python3
"""Fiches d'exercices à imprimer (PDF), par niveau et par volet.

Produit fiches/{cp,ce1,ce2,cm1}-{maths,lecture}.pdf : deux pages d'exercices,
une page de petits problèmes (maths) ou de textes à comprendre (lecture),
puis un corrigé pour les parents.

Les mots, phrases, histoires et conjugaisons viennent du jeu lui-même
(index.html), lus par tools/donnees.js : il faut Node.js et reportlab.

    python3 tools/fiches.py            # série 1
    python3 tools/fiches.py --serie 2  # autres nombres, autres mots
"""
import argparse
import json
import random
import subprocess
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
FONTS = Path(__file__).resolve().parent / 'fonts'
pdfmetrics.registerFont(TTFont('Andika', str(FONTS / 'Andika-Regular.ttf')))
pdfmetrics.registerFont(TTFont('Andika-Bold', str(FONTS / 'Andika-Bold.ttf')))

INK = HexColor('#1d2f6f')
SOFT = HexColor('#55649a')
RED = HexColor('#e8737a')
PENCIL = HexColor('#ffc93c')
PALE = HexColor('#eef1fb')
LINE = HexColor('#c9d2ef')
W, H = A4
M = 42  # marge
NIVEAUX = {'cp': 'CP', 'ce1': 'CE1', 'ce2': 'CE2', 'cm1': 'CM1'}
SITE = 'medrfig-hue.github.io/MRF2026'


def fmt(n):
    """3514 -> « 3 514 » (espace fine insécable des milliers)."""
    s = f'{n:,}'.replace(',', ' ')
    return s


def dec(x):
    s = f'{round(x, 3):.3f}'.rstrip('0').rstrip('.')
    i, _, f = s.partition('.')
    return fmt(int(i)) + (',' + f if f else '')


# Nombres en lettres, orthographe rectifiée de 1990 (comme dans le jeu).
UN = ['zéro', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf', 'dix', 'onze', 'douze', 'treize', 'quatorze', 'quinze', 'seize']
DIZ = {2: 'vingt', 3: 'trente', 4: 'quarante', 5: 'cinquante', 6: 'soixante'}


def w99(n, last=True):
    if n < 17:
        return UN[n]
    if n < 20:
        return 'dix-' + UN[n - 10]
    t, u = divmod(n, 10)
    if t == 7:
        return 'soixante-' + ('et-onze' if u == 1 else w99(10 + u))
    if t == 8:
        return 'quatre-vingt-' + UN[u] if u else 'quatre-vingt' + ('s' if last else '')
    if t == 9:
        return 'quatre-vingt-' + w99(10 + u)
    return DIZ[t] + ('' if u == 0 else '-et-un' if u == 1 else '-' + UN[u])


def w999(n, last=True):
    c, r = divmod(n, 100)
    s = '' if c == 0 else 'cent' if c == 1 else UN[c] + '-cent' + ('s' if r == 0 and last else '')
    if r:
        s += ('-' if s else '') + w99(r, last)
    return s


def en_lettres(n):
    m, r = divmod(n, 1000)
    head = '' if m == 0 else 'mille' if m == 1 else w999(m, False) + '-mille'
    return head + (('-' if head else '') + w999(r) if r else '') or 'zéro'


class Fiche:
    """Une fiche A4 : en-tête, exercices numérotés qui passent à la page suivante si besoin, corrigé."""

    def __init__(self, path, niveau, volet):
        self.c = canvas.Canvas(str(path), pagesize=A4)
        self.c.setTitle(f'Le Cahier des Nombres – {NIVEAUX[niveau]} – {volet}')
        self.c.setAuthor('Le Cahier des Nombres')
        self.niveau, self.volet = niveau, volet
        self.page = 0
        self.num = 0
        self.key = []  # (titre, réponses)
        self.y = 0
        self.part = 'Exercices'
        self.new_page()

    # ---- mise en page -------------------------------------------------
    def new_page(self):
        if self.page:
            self.c.showPage()
        self.page += 1
        c = self.c
        c.setFillColor(INK)
        c.roundRect(M, H - M - 34, W - 2 * M, 34, 8, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont('Andika-Bold', 15)
        c.drawString(M + 14, H - M - 23, f'Le Cahier des {"Nombres" if self.volet == "Maths" else "Mots"} · {self.part}')
        c.setFillColor(PENCIL)
        c.roundRect(W - M - 96, H - M - 28, 84, 22, 11, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont('Andika-Bold', 12)
        c.drawCentredString(W - M - 54, H - M - 21, f'{NIVEAUX[self.niveau]} · {self.volet}')
        c.setFont('Andika', 11)
        c.setFillColor(SOFT)
        c.drawString(M, H - M - 56, 'Prénom : ' + '.' * 48)
        c.drawString(W / 2 + 20, H - M - 56, 'Date : ' + '.' * 34)
        c.setFont('Andika', 8.5)
        c.drawString(M, M - 18, f'Le Cahier des Nombres · fiches à imprimer · {SITE}')
        c.drawRightString(W - M, M - 18, f'page {self.page}')
        self.y = H - M - 82

    def tag(self):
        short = {'Exercices': 'Exercice', 'Petits problèmes': 'Problème', 'Je lis et je comprends': 'Texte'}
        return f'{short.get(self.part, self.part)} {self.num}'

    def need(self, h):
        if self.y - h < M + 6:
            self.new_page()

    def section(self, title):
        self.part = title
        self.num = 0
        self.new_page()

    def text(self, s, x=None, size=12.5, font='Andika', color=INK, width=None, lead=None):
        x = M if x is None else x
        width = width or (W - M - x)
        lead = lead or size * 1.35
        lines = simpleSplit(s, font, size, width)
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        for ln in lines:
            self.c.drawString(x, self.y - size, ln)
            self.y -= lead
        return len(lines) * lead

    def ex(self, consigne, h_body, answers):
        """Ouvre un exercice : consigne numérotée. h_body = hauteur estimée du contenu."""
        lines = simpleSplit(consigne, 'Andika-Bold', 13, W - 2 * M - 30)
        self.need(len(lines) * 17 + h_body + 14)
        self.num += 1
        c = self.c
        c.setFillColor(RED)
        c.circle(M + 9, self.y - 9, 10, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont('Andika-Bold', 12)
        c.drawCentredString(M + 9, self.y - 13, str(self.num))
        self.text(consigne, x=M + 28, size=13, font='Andika-Bold', lead=17)
        self.y -= 6
        self.key.append((self.tag(), answers))

    def grid(self, items, cols, row_h, draw):
        """Place des items en colonnes ; draw(x, y_haut, largeur, item, index)."""
        cw = (W - 2 * M) / cols
        for i, it in enumerate(items):
            if i % cols == 0:
                if i:
                    self.y -= row_h
                self.need(row_h)
            draw(M + (i % cols) * cw, self.y, cw, it, i)
        self.y -= row_h + 10

    def dots(self, x, y, w):
        self.c.setStrokeColor(LINE)
        self.c.setDash(1, 2.5)
        self.c.line(x, y, x + w, y)
        self.c.setDash()

    def box(self, x, y, w, h, fill=None):
        self.c.setStrokeColor(LINE)
        self.c.setLineWidth(1.2)
        if fill:
            self.c.setFillColor(fill)
        self.c.roundRect(x, y, w, h, 6, fill=1 if fill else 0, stroke=1)
        self.c.setLineWidth(1)

    # ---- briques réutilisables ---------------------------------------
    def calc(self, consigne, items, cols=3, size=15):
        """items : (énoncé avec « … » pour la case, réponse)."""
        self.ex(consigne, 34, ' · '.join(f'{q.replace("…", str(a))}' for q, a in items))

        def draw(x, y, w, it, i):
            q = it[0]
            self.c.setFont('Andika', size)
            self.c.setFillColor(INK)
            before, _, after = q.partition('…')
            self.c.drawString(x + 4, y - 20, before)
            bx = x + 4 + pdfmetrics.stringWidth(before, 'Andika', size)
            self.box(bx + 2, y - 26, 44, 24)
            self.c.setFillColor(INK)
            self.c.drawString(bx + 52, y - 20, after)
        self.grid(items, cols, 34, draw)

    def choose(self, consigne, items, cols=1, size=13):
        """items : (phrase avec ___, [choix], réponse). L'enfant écrit le bon mot."""
        self.ex(consigne, 30, ' · '.join(a for _, _, a in items))

        def draw(x, y, w, it, i):
            s, ch, _ = it
            self.c.setFont('Andika', size)
            self.c.setFillColor(INK)
            parts = s.split('___')
            cx = x + 4
            for j, p in enumerate(parts):
                self.c.drawString(cx, y - 18, p)
                cx += pdfmetrics.stringWidth(p, 'Andika', size)
                if j < len(parts) - 1:
                    self.dots(cx + 3, y - 20, 62)
                    cx += 68
            self.c.setFillColor(SOFT)
            self.c.setFont('Andika', size - 2)
            self.c.drawString(cx + 10, y - 18, '(' + ' / '.join(ch) + ')')
        self.grid(items, cols, 28, draw)

    def write(self, consigne, prompts, answers, label_w=None, size=13):
        """Une ligne pointillée à remplir après chaque amorce."""
        self.ex(consigne, 30, ' · '.join(answers))

        def draw(x, y, w, it, i):
            self.c.setFont('Andika', size)
            self.c.setFillColor(INK)
            self.c.drawString(x + 4, y - 18, it)
            lw = label_w or pdfmetrics.stringWidth(it, 'Andika', size) + 10
            self.dots(x + 4 + lw, y - 20, w - lw - 12)
        self.grid(prompts, 1, 30, draw)

    def circle_words(self, consigne, words, answer, cols=5):
        self.ex(consigne, 36, answer)

        def draw(x, y, w, it, i):
            self.box(x + 4, y - 30, w - 12, 26, PALE)
            self.c.setFillColor(INK)
            self.c.setFont('Andika', 14)
            self.c.drawCentredString(x + w / 2 - 2, y - 22, it)
        self.grid(words, cols, 34, draw)

    def problem(self, text, answer, unit=''):
        lines = simpleSplit(text, 'Andika', 13, W - 2 * M - 30)
        self.need(len(lines) * 18 + 100)
        self.num += 1
        c = self.c
        c.setFillColor(PENCIL)
        c.circle(M + 9, self.y - 9, 10, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont('Andika-Bold', 12)
        c.drawCentredString(M + 9, self.y - 13, str(self.num))
        self.text(text, x=M + 28, size=13, lead=18)
        self.y -= 4
        self.box(M + 28, self.y - 60, W - 2 * M - 28, 60)
        c.setFont('Andika', 9.5)
        c.setFillColor(SOFT)
        c.drawString(M + 36, self.y - 13, 'Je cherche (dessin, schéma, calcul) :')
        self.y -= 78
        c.setFont('Andika-Bold', 12.5)
        c.setFillColor(INK)
        c.drawString(M + 28, self.y, 'Ma réponse :')
        self.dots(M + 112, self.y - 2, W - 2 * M - 112 - 40)
        c.setFont('Andika', 12)
        c.drawString(W - M - 34, self.y, unit)
        self.y -= 20
        self.key.append((self.tag(), answer))

    def reading(self, text, questions):
        """Texte encadré puis questions (choix à entourer ou réponse écrite)."""
        lines = simpleSplit(text, 'Andika', 13, W - 2 * M - 28)
        h = len(lines) * 18 + 18
        self.need(h + 60)
        self.num += 1
        y0 = self.y
        self.c.setFillColor(PALE)
        self.c.rect(M, y0 - h, W - 2 * M, h, fill=1, stroke=0)
        self.c.setFillColor(RED)
        self.c.rect(M, y0 - h, 4, h, fill=1, stroke=0)
        self.y -= 9
        self.text(text, x=M + 16, size=13, lead=18, width=W - 2 * M - 28)
        self.y = y0 - h - 14
        ans = []
        for k, (q, choices, a) in enumerate(questions, 1):
            self.need(52)
            self.text(f'{k}. {q}', size=12.5, font='Andika-Bold', lead=17)
            if choices:
                self.c.setFont('Andika', 12)
                self.c.setFillColor(INK)
                x = M + 18
                for ch in choices:
                    tw = pdfmetrics.stringWidth(ch, 'Andika', 12)
                    if x + tw > W - M:
                        self.y -= 20
                        x = M + 18
                    self.c.drawString(x, self.y - 13, ch)
                    x += tw + 26
                self.y -= 26
            else:
                self.dots(M + 18, self.y - 16, W - 2 * M - 18)
                self.y -= 28
            ans.append(f'{k}. {a}')
        self.y -= 8
        self.key.append((self.tag(), ' · '.join(ans)))

    # ---- dessins -----------------------------------------------------
    def tenframe(self, x, y, n, frames=None, cell=13):
        frames = frames or max(1, -(-n // 10))
        c = self.c
        for f in range(frames):
            fx = x + f * (5 * cell + 6)
            for i in range(10):
                cx, cy = fx + (i % 5) * cell, y - (i // 5 + 1) * cell
                c.setStrokeColor(INK)
                c.rect(cx, cy, cell, cell, fill=0, stroke=1)
                if f * 10 + i < n:
                    c.setFillColor(RED)
                    c.circle(cx + cell / 2, cy + cell / 2, cell / 2 - 2.5, fill=1, stroke=0)

    def base10(self, x, y, n, unit=5):
        c = self.c
        cent, d, u = n // 100, n // 10 % 10, n % 10
        c.setStrokeColor(INK)
        for k in range(cent):
            c.setFillColor(HexColor('#ffd2c4'))
            c.rect(x, y - 10 * unit, 10 * unit, 10 * unit, fill=1, stroke=1)
            x += 10 * unit + 5
        for k in range(d):
            c.setFillColor(HexColor('#cfeaff'))
            c.rect(x, y - 10 * unit, unit, 10 * unit, fill=1, stroke=1)
            for j in range(1, 10):
                c.line(x, y - j * unit, x + unit, y - j * unit)
            x += unit + 3
        x += 6
        for k in range(u):
            c.setFillColor(HexColor('#d5f5cf'))
            c.rect(x + (k % 3) * (unit + 2), y - 10 * unit + (k // 3) * (unit + 2), unit, unit, fill=1, stroke=1)

    def coins(self, x, y, values):
        c = self.c
        for v in values:
            if v <= 2:
                c.setFillColor(HexColor('#e9c75b') if v == 2 else HexColor('#d4d7dc'))
                c.setStrokeColor(SOFT)
                c.circle(x + 13, y - 14, 13, fill=1, stroke=1)
                c.setFillColor(INK)
                c.setFont('Andika-Bold', 10)
                c.drawCentredString(x + 13, y - 18, f'{v} €')
                x += 31
            else:
                c.setFillColor({5: HexColor('#d6dade'), 10: HexColor('#f6c4c1'), 20: HexColor('#c7d9f3'), 50: HexColor('#f8d6ad')}[v])
                c.setStrokeColor(SOFT)
                c.roundRect(x, y - 26, 46, 24, 3, fill=1, stroke=1)
                c.setFillColor(INK)
                c.setFont('Andika-Bold', 10)
                c.drawCentredString(x + 23, y - 18, f'{v} €')
                x += 52

    def fbar(self, x, y, n, k, w=150, h=20):
        c = self.c
        c.setStrokeColor(INK)
        for i in range(n):
            c.setFillColor(PENCIL if i < k else white)
            c.rect(x + i * w / n, y - h, w / n, h, fill=1, stroke=1)

    def posee(self, x, y, a, b, op):
        """Cadre quadrillé pour poser une opération."""
        c = self.c
        n = max(len(str(a)), len(str(b))) + (3 if op == '×' else 2)
        rows = 7 if op == '×' else 5
        cell = 16
        c.setStrokeColor(LINE)
        for i in range(n + 1):
            c.line(x + i * cell, y, x + i * cell, y - rows * cell)
        for j in range(rows + 1):
            c.line(x, y - j * cell, x + n * cell, y - j * cell)
        c.setFont('Andika', 13)
        c.setFillColor(INK)
        for row, s in ((1, str(a)), (2, str(b))):
            for k, ch in enumerate(reversed(s)):
                c.drawCentredString(x + (n - 1 - k) * cell + cell / 2, y - row * cell + 4, ch)
        c.drawCentredString(x + cell / 2, y - 2 * cell + 4, op)
        c.setStrokeColor(INK)
        c.setLineWidth(1.6)
        c.line(x, y - 2 * cell - 3, x + n * cell, y - 2 * cell - 3)
        c.setLineWidth(1)

    def corrige(self):
        self.part = 'Corrigé'
        self.new_page()
        self.text('Pour les parents : les réponses, exercice par exercice. Pour les dessins et les opérations posées, vérifiez le résultat.', size=11, color=SOFT)
        self.y -= 6
        for title, ans in self.key:
            lines = simpleSplit(ans, 'Andika', 11, W - 2 * M - 120)
            self.need(len(lines) * 14 + 8)
            self.c.setFont('Andika-Bold', 11)
            self.c.setFillColor(RED)
            self.c.drawString(M, self.y - 11, title)
            self.text(ans, x=M + 120, size=11, lead=14)
            self.y -= 6

    def save(self):
        self.corrige()
        self.c.save()


# =====================================================================
# MATHS
# =====================================================================
def pieces(R, allowed, total_max):
    p, s = [], 0
    target = R.randint(total_max // 3, total_max)
    for _ in range(40):
        v = R.choice(allowed)
        if s + v <= total_max:
            p.append(v)
            s += v
        if s >= target:
            break
    return sorted(p, reverse=True), s


def train(F, R, step, start_range, n_rows=3, show=fmt):
    rows, ans = [], []
    for _ in range(n_rows):
        start = R.randint(*start_range)
        if step < 0:
            start = max(start, -5 * step)
        seq = [round(start + i * step, 3) for i in range(6)]
        holes = sorted(R.sample(range(1, 6), 2))
        rows.append((seq, holes))
        ans.append(' et '.join(show(seq[h]) for h in holes))
    sign = f'+ {show(step)}' if step > 0 else f'− {show(-step)}'
    F.ex(f'Complète le train des nombres ({sign} à chaque wagon).', 40 * n_rows, ' · '.join(ans))
    for seq, holes in rows:
        F.need(40)
        x = M + 6
        for i, v in enumerate(seq):
            F.box(x, F.y - 30, 66, 26, PENCIL if i == 0 else None)
            if i not in holes:
                F.c.setFillColor(INK)
                F.c.setFont('Andika-Bold', 13)
                F.c.drawCentredString(x + 33, F.y - 22, show(v))
            x += 78
        F.y -= 40
    F.y -= 6


def compare(F, R, pairs, consigne='Écris <, > ou =.'):
    ans = []
    for a, b in pairs:
        ans.append('<' if a < b else '>' if a > b else '=')
    F.ex(consigne, 34, ' · '.join(ans))

    def draw(x, y, w, it, i):
        a, b, sa, sb = it
        F.c.setFont('Andika', 15)
        F.c.setFillColor(INK)
        F.c.drawRightString(x + w / 2 - 16, y - 20, sa)
        F.c.setStrokeColor(LINE)
        F.c.circle(x + w / 2, y - 15, 11, fill=0, stroke=1)
        F.c.drawString(x + w / 2 + 16, y - 20, sb)
    F.grid([(a, b, sa, sb) for (a, b), (sa, sb) in zip(pairs, [(fmt(a) if isinstance(a, int) else dec(a), fmt(b) if isinstance(b, int) else dec(b)) for a, b in pairs])], 2, 32, draw)


def maths(F, R, niv, kids):
    def kid():
        return R.choice(kids)

    if niv == 'cp':
        items = [R.randint(3, 20) for _ in range(6)]
        F.ex('Compte les points et écris le nombre.', 70, ' · '.join(map(str, items)))

        def draw_tf(x, y, w, n, i):
            F.tenframe(x + 6, y - 2, n, 2, 12)
            F.box(x + 150, y - 32, 26, 26)
        F.grid(items, 2, 46, draw_tf)
        F.calc('Calcule.', [(f'{a} + {b} = …', a + b) for a, b in [(R.randint(1, 6), R.randint(1, 4)) for _ in range(6)] + [(R.randint(6, 12), R.randint(2, 8)) for _ in range(3)]])
        F.calc('Calcule.', [(f'{a} − {b} = …', a - b) for a, b in [(lambda a: (a, R.randint(1, a - 1)))(R.randint(4, 10)) for _ in range(6)] + [(lambda a: (a, R.randint(1, 9)))(R.randint(11, 19)) for _ in range(3)]])
        F.calc('Complète pour faire 10.', [(f'{a} + … = 10', 10 - a) for a in R.sample(range(1, 10), 6)])
        compare(F, R, [(R.randint(0, 30), R.randint(0, 30)) for _ in range(5)] + [(12, 21)])
        ns = [R.randint(11, 59) for _ in range(3)]
        F.ex('Combien de dizaines et d\'unités ? Écris le nombre.', 70, ' · '.join(f'{n // 10} d {n % 10} u = {n}' for n in ns))
        for n in ns:
            F.need(64)
            F.base10(M + 10, F.y, n, 5)
            F.c.setFont('Andika', 13)
            F.c.setFillColor(INK)
            F.c.drawString(M + 290, F.y - 32, '…… dizaines  …… unités  =  ……')
            F.y -= 62
        train(F, R, 1, (0, 14), 2)
        train(F, R, 10, (0, 9), 1)
        sets = [pieces(R, [1, 2, 5, 10], 20) for _ in range(3)]
        F.ex('Combien d\'euros ?', 40, ' · '.join(f'{s} €' for _, s in sets))
        for p, _ in sets:
            F.need(38)
            F.coins(M + 10, F.y, p)
            F.c.setFont('Andika', 13)
            F.c.setFillColor(INK)
            F.c.drawString(W - M - 90, F.y - 18, '…… €')
            F.y -= 38
        F.section('Petits problèmes')
        probs = []
        for kind in ['gain', 'perte', 'reunion', 'plus', 'perte', 'groupes']:
            N, p = kid()
            o = R.choice(['billes', 'bonbons', 'images', 'crayons'])
            if kind == 'gain':
                a, b = R.randint(3, 9), R.randint(2, 9)
                probs.append((f'{N} a {a} {o}. {p.capitalize()} en gagne {b}. Combien de {o} a-t-{p} maintenant ?', f'{a} + {b} = {a + b} {o}'))
            elif kind == 'perte':
                a = R.randint(6, 15)
                b = R.randint(1, a - 2)
                probs.append((f'{N} a {a} {o}. {p.capitalize()} en perd {b}. Combien de {o} lui reste-t-il ?', f'{a} − {b} = {a - b} {o}'))
            elif kind == 'reunion':
                a, b = R.randint(2, 9), R.randint(2, 9)
                M2 = kid()[0]
                probs.append((f'{N} a {a} {o}. {M2} en a {b}. Combien de {o} ont-ils ensemble ?', f'{a} + {b} = {a + b} {o}'))
            elif kind == 'plus':
                a, b = R.randint(3, 10), R.randint(2, 6)
                M2 = kid()[0]
                probs.append((f'{N} a {a} {o}. {M2} en a {b} de plus. Combien de {o} a {M2} ?', f'{a} + {b} = {a + b} {o}'))
            else:
                g, n = R.randint(2, 4), R.choice([2, 5])
                probs.append((f'Il y a {g} assiettes. Sur chaque assiette, il y a {n} fraises. Combien de fraises y a-t-il en tout ?', f'{" + ".join([str(n)] * g)} = {g * n} fraises'))
        for t, a in probs:
            F.problem(t, a)

    elif niv == 'ce1':
        F.calc('Calcule.', [(f'{a} + {b} = …', a + b) for a, b in [(R.randint(12, 68), R.randint(11, 29)) for _ in range(6)]])
        F.calc('Calcule.', [(f'{a} − {b} = …', a - b) for a, b in [(lambda a: (a, R.randint(3, a - 10)))(R.randint(25, 99)) for _ in range(6)]])
        ops = [(R.randint(25, 68), R.randint(16, 31), '+'), (R.randint(40, 79), R.randint(14, 39), '+'), (R.randint(52, 98), R.randint(17, 45), '−')]
        F.ex('Pose et calcule.', 96, ' · '.join(f'{a} {o} {b} = {a + b if o == "+" else a - b}' for a, b, o in ops))
        F.need(96)
        for k, (a, b, o) in enumerate(ops):
            F.posee(M + 20 + k * 170, F.y, a, b, o)
        F.y -= 100
        F.calc('Complète pour faire 100.', [(f'{a} + … = 100', 100 - a) for a in [R.randint(1, 9) * 10 for _ in range(3)] + [R.randint(11, 89) for _ in range(3)]])
        F.calc('Les tables.', [(f'{k} × {t} = …', k * t) for t, k in [(R.choice([2, 3, 4, 5, 10]), R.randint(1, 10)) for _ in range(9)]])
        dbl = [(f'Le double de {n} = …', 2 * n) for n in R.sample(range(5, 30), 3)] + [(f'La moitié de {2 * n} = …', n) for n in R.sample(range(3, 25), 3)]
        F.calc('Doubles et moitiés.', dbl, cols=2, size=14)
        ns = [R.randint(101, 999) for _ in range(4)]
        F.write('Décompose en centaines, dizaines et unités.', [f'{n} = …… c  …… d  …… u' for n in ns], [f'{n} = {n // 100} c {n // 10 % 10} d {n % 10} u' for n in ns], label_w=260)
        n = R.choice([123, 345, 517, 284])
        compare(F, R, [(R.randint(100, 999), R.randint(100, 999)) for _ in range(5)] + [(n, int(str(n)[::-1]))])
        train(F, R, R.choice([2, 5]), (0, 40), 1)
        train(F, R, 10, (3, 60), 1)
        train(F, R, 100, (100, 400), 1)
        F.section('Petits problèmes')
        o = R.choice(['billes', 'images', 'cartes'])
        N, p = kid()
        M2, p2 = kid()
        a, b = R.randint(15, 45), R.randint(12, 38)
        F.problem(f'{N} a {a} {o}. {p.capitalize()} en gagne {b} à la récréation. Combien de {o} a-t-{p} maintenant ?', f'{a} + {b} = {a + b} {o}')
        a = R.randint(40, 90)
        b = R.randint(12, a - 10)
        F.problem(f'Dans le bus, il y a {a} passagers. À l\'arrêt, {b} passagers descendent. Combien reste-t-il de passagers ?', f'{a} − {b} = {a - b} passagers')
        a, b = R.randint(15, 40), R.randint(41, 80)
        F.problem(f'{N} a {a} {o}. {M2} en a {b}. Combien de {o} {M2} a-t-{p2} de plus que {N} ?', f'{a} + {b - a} = {b}, donc {b - a} {o} de plus')
        k, n = R.randint(3, 5), R.choice([4, 5, 10])
        F.problem(f'Il y a {k} boîtes de {n} œufs. Combien d\'œufs y a-t-il en tout ?', f'{k} × {n} = {k * n} œufs')
        pay, price = R.choice([20, 50]), 0
        price = R.randint(5, pay - 3)
        F.problem(f'{N} achète un livre à {price} €. {p.capitalize()} paie avec un billet de {pay} €. Combien le marchand lui rend-il ?', f'{price} + {pay - price} = {pay}, on lui rend {pay - price} €', '€')
        k, n = R.choice([2, 3, 4]), R.randint(3, 6)
        F.problem(f'{N} partage {k * n} bonbons entre {k} amis. Chacun en reçoit autant. Combien de bonbons chaque ami reçoit-il ?', f'{k} × {n} = {k * n}, donc {n} bonbons chacun')

    elif niv == 'ce2':
        ops = [(R.randint(150, 650), R.randint(120, 340), '+'), (R.randint(250, 580), R.randint(160, 410), '+'), (R.randint(420, 980), R.randint(130, 400), '−'), (R.randint(500, 990), R.randint(150, 480), '−')]
        F.ex('Pose et calcule.', 96, ' · '.join(f'{a} {o} {b} = {a + b if o == "+" else a - b}' for a, b, o in ops))
        F.need(96)
        for k, (a, b, o) in enumerate(ops):
            F.posee(M + 6 + k * 130, F.y, a, b, o)
        F.y -= 100
        F.calc('Les tables.', [(f'{k} × {t} = …', k * t) for t, k in [(R.randint(2, 9), R.randint(2, 10)) for _ in range(12)]])
        mul = [(R.randint(12, 49), R.randint(2, 5)) for _ in range(4)] + [(R.randint(2, 99), R.choice([10, 100])) for _ in range(2)]
        F.calc('Multiplie.', [(f'{a} × {b} = …', fmt(a * b)) for a, b in mul])
        dv = [(R.randint(2, 9), R.randint(2, 10)) for _ in range(6)]
        F.calc('Divise.', [(f'{t * q} : {t} = …', q) for t, q in dv])
        ns = [R.randint(1001, 9999) for _ in range(2)] + [R.randint(101, 999) * 10 for _ in range(1)] + [R.randint(1, 9) * 1000 + R.randint(1, 99)]
        F.write('Écris ces nombres en chiffres.', [en_lettres(n) for n in ns], [fmt(n) for n in ns], size=12)
        lists = [sorted(R.sample(range(1000, 9999), 5), key=lambda _: R.random()) for _ in range(2)]
        F.write('Range du plus petit au plus grand.', ['  ;  '.join(fmt(n) for n in l) for l in lists], [' < '.join(fmt(n) for n in sorted(l)) for l in lists])
        F.calc('Complète pour faire 1 000.', [(f'{fmt(a)} + … = 1 000', fmt(1000 - a)) for a in [R.randint(1, 9) * 100 for _ in range(2)] + [R.randint(1, 99) * 10 for _ in range(2)] + [R.randint(101, 899) for _ in range(2)]], cols=2)
        compare(F, R, [(R.randint(1000, 9999), R.randint(1000, 9999)) for _ in range(4)] + [(R.randint(5, 9) * R.randint(3, 9), R.randint(15, 81)) for _ in range(2)])
        train(F, R, R.choice([25, 50]), (0, 20), 1)
        train(F, R, 1000, (100, 3000), 1)
        F.section('Petits problèmes')
        N, p = kid()
        M2, p2 = kid()
        a, b = R.randint(150, 600), R.randint(35, 300)
        F.problem(f'{N} a {a} timbres dans sa collection. {p.capitalize()} en reçoit {b} pour son anniversaire. Combien de timbres a-t-{p} maintenant ?', f'{a} + {b} = {a + b} timbres')
        a, b = R.randint(3, 9), R.randint(6, 25)
        F.problem(f'Un fleuriste prépare {a} bouquets de {b} roses. Combien de roses utilise-t-il ?', f'{a} × {b} = {a * b} roses')
        k, n = R.randint(3, 9), R.randint(3, 10)
        F.problem(f'On range {k * n} œufs dans des boîtes de {k}. Combien de boîtes remplit-on ?', f'{n} × {k} = {k * n}, donc {n} boîtes')
        a, b, c_ = R.randint(40, 150), R.randint(10, 60), R.randint(5, 35)
        F.problem(f'{N} a {a} billes. {p.capitalize()} en gagne {b}, puis en perd {c_}. Combien de billes a-t-{p} à la fin ?', f'{a} + {b} − {c_} = {a + b - c_} billes')
        n, price = R.randint(2, 6), R.randint(3, 15)
        pay = -(-n * price // 10) * 10 + 10
        F.problem(f'{M2} achète {n} livres à {price} € chacun. {p2.capitalize()} paie avec {pay} €. Combien d\'euros lui rend-on ?', f'{n} × {price} = {n * price} €, puis {pay} − {n * price} = {pay - n * price} €', '€')
        a, b = R.randint(120, 400), R.randint(410, 900)
        F.problem(f'Une école a {a} livres de contes et {b} albums. Combien d\'albums de plus que de livres de contes y a-t-il ?', f'{b} − {a} = {b - a} albums de plus')

    else:  # cm1
        ns = [R.randint(2, 999) * 1000 + R.choice([0, R.randint(1, 999), R.randint(1, 9) * 100]) for _ in range(4)]
        F.write('Écris ces nombres en chiffres.', [en_lettres(n) for n in ns], [fmt(n) for n in ns], size=11.5)
        ns2 = [R.randint(10000, 999999) for _ in range(2)]
        F.write('Écris ces nombres en lettres.', [fmt(n) for n in ns2], [en_lettres(n) for n in ns2], label_w=80)
        fr = [(R.choice([2, 3, 4, 5, 6, 8, 10]),) for _ in range(4)]
        fr = [(n, R.randint(1, n - 1)) for (n,) in fr]
        F.ex('Colorie la fraction demandée.', 60, 'vérifier : ' + ' · '.join(f'{k} part(s) sur {n}' for n, k in fr))

        def draw_col(x, y, w, it, i):
            n, k = it
            F.c.setFont('Andika-Bold', 14)
            F.c.setFillColor(INK)
            F.c.drawCentredString(x + 14, y - 10, str(k))
            F.c.line(x + 6, y - 14, x + 22, y - 14)
            F.c.drawCentredString(x + 14, y - 28, str(n))
            F.fbar(x + 34, y - 6, n, 0, w=w - 50)
        F.grid(fr, 2, 40, draw_col)
        fr2 = [(n, R.randint(1, n - 1)) for n in [R.choice([3, 4, 5, 6, 8, 10]) for _ in range(4)]]
        F.ex('Quelle fraction de la bande est coloriée ?', 40, ' · '.join(f'{k}/{n}' for n, k in fr2))

        def draw_q(x, y, w, it, i):
            n, k = it
            F.fbar(x + 6, y - 6, n, k, w=w - 70)
            F.box(x + w - 54, y - 34, 36, 30)
        F.grid(fr2, 2, 40, draw_q)
        fq = [(n, R.randint(1, n - 1), n * R.randint(2, 12)) for n in [R.choice([2, 3, 4, 5, 10]) for _ in range(6)]]
        F.calc('Calcule la fraction de la quantité.', [(f'{k}/{n} de {q} = …', q // n * k) for n, k, q in fq], cols=3, size=14)
        pairs = []
        for _ in range(6):
            i_, t = R.randint(0, 20), R.randint(2, 9)
            a = i_ + t / 10
            b = R.choice([i_ + (t - 1) / 10 + R.randint(1, 9) / 100, a, i_ + R.randint(1, 9) / 10])
            pairs.append((a, b))
        compare(F, R, pairs, 'Écris <, > ou = (attention aux chiffres après la virgule).')
        ops = [(R.randint(102, 899), R.randint(12, 49), '×'), (R.randint(1200, 8999), R.randint(1500, 9999), '+')]
        F.ex('Pose et calcule.', 96, ' · '.join(f'{fmt(a)} {o} {fmt(b)} = {fmt(a * b if o == "×" else a + b)}' for a, b, o in ops))
        F.need(124)
        F.posee(M + 20, F.y, ops[0][0], ops[0][1], '×')
        F.posee(M + 250, F.y, ops[1][0], ops[1][1], '+')
        F.y -= 124
        dv = [(R.randint(3, 9), R.randint(5, 25)) for _ in range(4)]
        dv = [(b, q, R.randint(1, b - 1)) for b, q in dv]
        F.write('Division avec reste : trouve le quotient et le reste.', [f'{b * q + r} = {b} × …… + ……' for b, q, r in dv], [f'{b * q + r} = {b} × {q} + {r}' for b, q, r in dv], label_w=150)
        conv = [('m', 'cm', 100), ('km', 'm', 1000), ('kg', 'g', 1000), ('L', 'cL', 100), ('h', 'min', 60), ('cm', 'mm', 10)]
        R.shuffle(conv)
        items = [(f'{n} {a} = … {b}', fmt(n * f)) for (a, b, f), n in zip(conv, [R.randint(2, 9) for _ in conv])]
        F.calc('Convertis.', items, cols=2, size=14)
        F.section('Petits problèmes')
        N, p = kid()
        price, has = R.randint(150, 600), 0
        has = R.randint(50, price - 20)
        F.problem(f'{N} veut acheter un vélo à {price} €. {p.capitalize()} a déjà économisé {has} €. Combien d\'euros lui manque-t-il ?', f'{price} − {has} = {price - has} €', '€')
        a, b = R.randint(12, 45), R.randint(12, 30)
        F.problem(f'Un théâtre a {a} rangées de {b} fauteuils. Combien de fauteuils y a-t-il en tout ?', f'{a} × {b} = {a * b} fauteuils')
        b, q, r = R.randint(4, 9), R.randint(5, 15), 0
        r = R.randint(1, b - 1)
        F.problem(f'On range {b * q + r} œufs dans des boîtes de {b}. Combien de boîtes pleines obtient-on ? Combien d\'œufs restent ?', f'{b * q + r} = {b} × {q} + {r} : {q} boîtes pleines, {r} œuf(s) restant(s)')
        n, Q = R.choice([3, 4, 5]), 0
        Q = n * R.randint(4, 12)
        F.problem(f'{N} a {Q} images. {p.capitalize()} en donne {["", "", "la moitié", "le tiers", "le quart", "le cinquième"][n]} à son frère. Combien d\'images lui reste-t-il ?', f'{Q} : {n} = {Q // n} données, {Q} − {Q // n} = {Q - Q // n} images')
        a, b = R.randint(8, 40), 0
        b = R.randint(5, a - 1)
        F.problem(f'Un jardin rectangulaire mesure {a} m de long et {b} m de large. Quelle longueur de grillage faut-il pour en faire le tour ?', f'{a} + {b} + {a} + {b} = {2 * (a + b)} m', 'm')
        d, m_ = R.choice([1, 2]), R.choice([15, 30, 45])
        F.problem(f'Un film commence à 14 h 20 et dure {d} h {m_} min. À quelle heure se termine-t-il ?', f'14 h 20 + {d} h {m_} = {14 + d + (20 + m_) // 60} h {(20 + m_) % 60:02d}')


# =====================================================================
# LECTURE
# =====================================================================
def lecture(F, R, niv, D):
    lex = D['lex']

    def story_qs(st, n=3):
        qs = R.sample(st['qs'], min(n, len(st['qs'])))
        out = []
        for q, a, pool in qs:
            ch = [a] + R.sample([x for x in pool if x != a], min(2, len([x for x in pool if x != a])))
            R.shuffle(ch)
            out.append((q + ' Entoure la bonne réponse.', ch, a))
        return out

    if niv == 'cp':
        letters = R.sample('bdpqmnfthagerl', 6)
        right = letters[:]
        R.shuffle(right)
        F.ex('Relie chaque majuscule à sa minuscule.', 6 * 26, ' · '.join(f'{l.upper()} – {l}' for l in letters))
        for k in range(6):
            F.c.setFont('Andika-Bold', 18)
            F.c.setFillColor(INK)
            F.c.drawString(M + 80, F.y - 18, letters[k].upper())
            F.c.circle(M + 110, F.y - 12, 3, fill=1, stroke=0)
            F.c.circle(M + 250, F.y - 12, 3, fill=1, stroke=0)
            F.c.drawString(M + 266, F.y - 18, right[k])
            F.y -= 26
        F.y -= 8
        for son, label in [('ou', 'ou'), ('an', 'an')]:
            yes = [x['w'] for x in lex if son in x['sons']]
            no = [x['w'] for x in lex if son not in x['sons']]
            words = R.sample(yes, 4) + R.sample(no, 6)
            R.shuffle(words)
            F.circle_words(f'Entoure les mots où tu entends le son [{label}].', words, ', '.join(w for w in words if w in yes))
        C = ['b', 'd', 'f', 'l', 'm', 'n', 'p', 'r', 's', 't', 'v', 'ch']
        V = ['a', 'i', 'o', 'u', 'é', 'e']
        syl = [(R.choice(C), R.choice(V)) for _ in range(9)]
        F.calc('Écris la syllabe.', [(f'{c} + {v} = …', c + v) for c, v in syl])
        cnt = [x for x in lex if x['w'] not in D['noCount'] and not x['syl'][-1].endswith('e')]
        words = R.sample(cnt, 10)
        F.ex('Compte les syllabes de chaque mot et écris le nombre.', 70, ' · '.join(f"{x['w']} : {len(x['syl'])}" for x in words))

        def draw_s(x, y, w, it, i):
            F.c.setFont('Andika', 14)
            F.c.setFillColor(INK)
            F.c.drawString(x + 6, y - 20, it['w'])
            F.box(x + w - 40, y - 28, 24, 24)
        F.grid(words, 3, 34, draw_s)
        rows = R.sample([x for x in lex if len(x['fautes']) >= 3], 5)
        F.ex('Entoure le mot bien écrit.', 30, ' · '.join(x['w'] for x in rows))
        for x in rows:
            ch = [x['w']] + x['fautes'][:3]
            R.shuffle(ch)
            F.need(28)
            F.c.setFont('Andika', 14)
            F.c.setFillColor(INK)
            for k, wd in enumerate(ch):
                F.c.drawString(M + 20 + k * 120, F.y - 18, wd)
            F.y -= 28
        F.y -= 6
        F.ex('Lis et dessine.', 130, 'Dessins : vérifier que chaque élément de la phrase est présent.')
        F.need(130)
        phrases = R.sample(['Je dessine un chat sous une table.', 'Je dessine trois ballons rouges.', 'Je dessine un soleil et deux nuages.', 'Je dessine une maison avec une porte verte.'], 2)
        for k, ph in enumerate(phrases):
            x = M + k * (W - 2 * M) / 2
            yy = F.y
            F.text(ph, x=x + 6, size=11.5, font='Andika-Bold', width=(W - 2 * M) / 2 - 20, lead=14)
            F.y = yy
            F.box(x + 6, F.y - 128, (W - 2 * M) / 2 - 16, 98)
        F.y -= 140
        F.section('Je lis et je comprends')
        pets = [('chat', 'il'), ('chien', 'il'), ('lapin', 'il')]
        for _ in range(3):
            N, p = R.choice(D['kids'])
            pet = R.choice(pets)[0]
            food = R.choice(['une pomme', 'une banane', 'du pain', 'une fraise'])
            col = R.choice(['rouge', 'bleu', 'vert', 'jaune'])
            text = f'{N} a un {pet}. Le {pet} joue avec un ballon {col}. Le soir, {N} mange {food}.'
            F.reading(text, [
                (f'Qui a un {pet} ?', [N] + R.sample([k[0] for k in D['kids'] if k[0] != N], 2), N),
                ('De quelle couleur est le ballon ?', R.sample(['rouge', 'bleu', 'vert', 'jaune'], 4), col),
                (f'Que mange {N} ?', R.sample(['une pomme', 'une banane', 'du pain', 'une fraise'], 4), food),
            ])
        return

    if niv == 'ce1':
        g = R.sample(D['graph'], 8)
        F.choose('Complète chaque mot avec le bon son.', [(x['pre'] + '___' + x['post'], sorted([x['ans']] + x['bad'][:2], key=lambda _: R.random()), x['ans']) for x in g], cols=2)
        nouns = R.sample(D['nouns'], 10)
        F.choose('Écris un ou une.', [('___ ' + n['w'], ['un', 'une'], 'un' if n['g'] == 'm' else 'une') for n in nouns], cols=2)
        nouns = R.sample(D['nouns'], 6)
        F.choose("Écris le, la ou l'.", [('___ ' + n['w'], ['le', 'la', "l'"], "l'" if n['w'][0] in 'aeéèêiou' else 'le' if n['g'] == 'm' else 'la') for n in nouns], cols=2)
        nouns = R.sample([n for n in D['nouns'] if n['p'] != n['w'] + 's'], 4) + R.sample([n for n in D['nouns'] if n['p'] == n['w'] + 's'], 2)
        R.shuffle(nouns)
        F.write('Écris au pluriel.', [f"{'un' if n['g'] == 'm' else 'une'} {n['w']} → des" for n in nouns], [n['p'] for n in nouns], label_w=170)
        sents = R.sample(D['sents'], 4)
        scr = []
        for s in sents:
            w = s.split(' ')
            w = [x if (i == 0 and x in D['proper']) or x in D['proper'] else x.lower() for i, x in enumerate(w)]
            R.shuffle(w)
            scr.append(' / '.join(w))
        F.write('Remets les mots dans l\'ordre et écris la phrase.', scr, [s + '.' for s in sents], label_w=250, size=12)
        lists = [R.sample([x['w'] for x in lex], 5) for _ in range(2)]
        F.write('Range ces mots dans l\'ordre alphabétique.', [' – '.join(l) for l in lists], [', '.join(sorted(l, key=lambda s: s.replace('é', 'e').replace('â', 'a'))) for l in lists], label_w=260)
        F.section('Je lis et je comprends')
        for idx in (0, 1, 0):
            st = R.choice(D['stories'][idx])
            F.reading(st['text'], story_qs(st))
        return

    if niv in ('ce2', 'cm1'):
        H = D['homo']
        keys = ['a/à', 'et/est', 'son/sont', 'on/ont'] if niv == 'ce2' else ['ou/où', 'ce/se', "c'est/s'est", 'ces/ses']
        for k in keys[:2]:
            F.choose(f'Complète avec {k.replace("/", " ou ")}.', [(s, [o.capitalize() if s.startswith('___') else o for o in k.split('/')], a) for s, a in R.sample(H[k], 5)], cols=1)
        mix = [(s, [o.capitalize() if s.startswith('___') else o for o in k.split('/')], a) for k in keys[2:] for s, a in R.sample(H[k], 3)]
        R.shuffle(mix)
        F.choose('Complète avec le bon mot.', mix, cols=1)
        persons = ['je', 'tu', 'il / elle', 'nous', 'vous', 'ils / elles']
        if niv == 'ce2':
            plan = [(R.choice(['chanter', 'jouer', 'danser', 'parler']), 'pr', 'au présent'), (R.choice(['être', 'avoir', 'aller', 'faire']), 'pr', 'au présent'),
                    (R.choice(['finir', 'chanter', 'jouer']), 'fu', 'au futur'), (R.choice(['regarder', 'danser', 'marcher']), 'im', "à l'imparfait")]
        else:
            plan = [(R.choice(['chanter', 'jouer', 'finir', 'prendre']), 'pc', 'au passé composé'), ('aller', 'pc', 'au passé composé (avec être)'),
                    (R.choice(['venir', 'pouvoir', 'voir', 'dire']), 'pr', 'au présent'), (R.choice(['venir', 'pouvoir', 'voir', 'faire']), 'fu', 'au futur')]
        F.ex('Conjugue les verbes.', 150, ' — '.join(f"{v} {lab} : " + ', '.join(D['conj'][v][t]) for v, t, lab in plan))
        F.need(170)
        colw = (W - 2 * M) / 2
        y0 = F.y
        for k, (v, t, lab) in enumerate(plan):
            x = M + (k % 2) * colw
            yy = y0 - (k // 2) * 165
            F.c.setFont('Andika-Bold', 12.5)
            F.c.setFillColor(RED)
            F.c.drawString(x + 6, yy - 14, f'{v} {lab}')
            F.c.setFont('Andika', 12.5)
            F.c.setFillColor(INK)
            for j, pr in enumerate(persons):
                F.c.drawString(x + 10, yy - 36 - j * 21, pr)
                F.dots(x + 74, yy - 38 - j * 21, colw - 96)
        F.y = y0 - 2 * 165 - 4
        if niv == 'ce2':
            items = []
            for sg, pl, g in R.sample(D['nounsA'], 6):
                a = R.choice(D['adj'])
                plural = R.random() < .5
                forms = {'ms': a, 'fs': a + 'e', 'mp': a if a.endswith('s') else a + 's', 'fp': a + 'es'}
                ans = forms[g + ('p' if plural else 's')]
                det = 'Les' if plural else ('La' if g == 'f' else 'Le')
                items.append((f"{det} {pl if plural else sg} {'sont' if plural else 'est'} ___.", [a], ans))
            F.choose("Accorde l'adjectif entre parenthèses.", items, cols=2)
        else:
            items = []
            for S, g, n in R.sample(D['subjPP'], 6):
                pp = R.choice(['parti', 'arrivé', 'tombé', 'venu', 'resté'])
                items.append((f"{S} {'sont' if n == 'p' else 'est'} ___ hier.", [pp], pp + {'ms': '', 'fs': 'e', 'mp': 's', 'fp': 'es'}[g + n]))
            F.choose('Accorde le participe passé.', items, cols=1)
        bank = D['tagged'] + (D['taggedP'] if niv == 'cm1' else [])
        ss = R.sample(bank, 5)
        if niv == 'ce2':
            cons, cats, names = 'Souligne le verbe et entoure le nom (ou les noms).', ['v', 'n'], ['verbe', 'nom']
        else:
            cons, cats, names = 'Souligne les déterminants et entoure les pronoms.', ['d', 'p'], ['déterminant', 'pronom']
        ans = []
        for s in ss:
            toks = [t.split('/') for t in s.split(' ')]
            ans.append(' ; '.join(f"{nm} : {', '.join(w for w, c in toks if c == ct) or '—'}" for ct, nm in zip(cats, names)))
        F.ex(cons, 30 * len(ss), ' | '.join(ans))
        for s in ss:
            F.need(28)
            F.c.setFont('Andika', 15)
            F.c.setFillColor(INK)
            F.c.drawString(M + 20, F.y - 18, ' '.join(t.split('/')[0] for t in s.split(' ')) + '.')
            F.y -= 30
        F.y -= 6
        if niv == 'ce2':
            pairs = R.sample(D['ant'], 6)
            right = [b for _, b in pairs]
            R.shuffle(right)
            F.ex('Relie chaque mot à son contraire.', 6 * 26, ' · '.join(f'{a} – {b}' for a, b in pairs))
            for k, (a, _) in enumerate(pairs):
                F.c.setFont('Andika', 14)
                F.c.setFillColor(INK)
                F.c.drawString(M + 60, F.y - 18, a)
                F.c.circle(M + 170, F.y - 12, 3, fill=1, stroke=0)
                F.c.circle(M + 300, F.y - 12, 3, fill=1, stroke=0)
                F.c.drawString(M + 316, F.y - 18, right[k])
                F.y -= 26
            F.y -= 8
            groups = {}
            for x in lex:
                groups.setdefault(x['w'][0], []).append(x['w'])
            big = [g for g in groups.values() if len(g) >= 5]
            lists = [R.sample(g, 5) for g in R.sample(big, 2)]
            F.write("Range dans l'ordre alphabétique (regarde la 2e lettre).", [' – '.join(l) for l in lists], [', '.join(sorted(l, key=lambda s: s.replace('é', 'e').replace('â', 'a'))) for l in lists], label_w=260)
        else:
            pref = R.sample(D['pref'], 8)
            F.calc('Écris le contraire en ajoutant un préfixe.', [(f'{a} → …', b) for a, b in pref], cols=2, size=13)
            fam = R.sample(D['familles'], 4)
            rows = []
            for w, a, bad in fam:
                ws = [w, a, bad[0]]
                R.shuffle(ws)
                rows.append((ws, bad[0]))
            F.ex("Barre l'intrus : le mot qui n'est pas de la même famille.", 30 * len(rows), ' · '.join(i for _, i in rows))
            for ws, _ in rows:
                F.need(28)
                F.c.setFont('Andika', 14)
                F.c.setFillColor(INK)
                for k, wd in enumerate(ws):
                    F.c.drawString(M + 30 + k * 140, F.y - 18, wd)
                F.y -= 28
            F.y -= 6
        F.section('Je lis et je comprends')
        idxs = (2, 3) if niv == 'ce2' else (4, 2, 3)
        for idx in idxs:
            st = R.choice(D['stories'][idx])
            F.reading(st['text'], story_qs(st, 3 if niv == 'ce2' else 4))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--serie', type=int, default=1, help='numéro de série : change les nombres et les mots (défaut : 1)')
    ap.add_argument('--sortie', default=str(ROOT / 'fiches'), help='dossier de sortie')
    args = ap.parse_args()
    out = Path(args.sortie)
    out.mkdir(parents=True, exist_ok=True)
    D = json.loads(subprocess.run(['node', str(ROOT / 'tools' / 'donnees.js'), str(args.serie)], capture_output=True, check=True, text=True).stdout)
    for i, niv in enumerate(NIVEAUX):
        for j, (volet, fn) in enumerate((('Maths', maths), ('Lecture', lecture))):
            R = random.Random(args.serie * 1000 + i * 10 + j)
            F = Fiche(out / f'{niv}-{volet.lower()}.pdf', niv, volet)
            fn(F, R, niv, D['kids'] if volet == 'Maths' else D)
            F.save()
            print(f'{niv}-{volet.lower()}.pdf : {F.page} pages')


if __name__ == '__main__':
    main()
