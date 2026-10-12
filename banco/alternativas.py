"""Leitor das alternativas para as provas com fonte quebrada (2014 e 2017).

Nesses dois arquivos a fonte embutida não tem ToUnicode: o `pdftotext` devolve
glifos trocados ("ĚĞ" no lugar de "da"). Duas saídas do poppler, porém, ainda
funcionam, porque não dependem de ler o TEXTO — só a GEOMETRIA:

1. `pdftotext -bbox-layout` devolve a caixa de cada palavra, e as LETRAS das
   alternativas (A…E) vêm legíveis, porque vêm de outra fonte, a dos símbolos,
   que tem ToUnicode. Elas também são mais ALTAS que o corpo do texto
   (15.6 pt contra 12.3), então dá para reconhecê-las sem ambiguidade;
2. renderizar a página e passar no tesseract devolve o TEXTO certo.

Aqui juntamos os dois: a geometria diz ONDE começa cada alternativa e QUAL
letra é; o OCR diz o que está escrito. Assim a letra nunca vem "de ordem" (o
erro do OCR puro, que às vezes perde a 5ª bolinha e desloca as letras).
"""

import re
import subprocess
import sys
import unicodedata

sys.path.insert(0, '/root/enade-simulado/banco')
import layout

FONTE = '/root/enade-simulado/fontes/'

# altura do glifo da letra-da-alternativa contra o corpo do texto (em pontos,
# medido nestas provas: 15.6 contra 12.3)
H_ALTERNATIVA = (13.5, 17.5)

_cache = {}


def geometria(pdf):
    """-> [(pagina, [(x0, y0, x1, y1, texto), ...])] por página."""
    if pdf in _cache:
        return _cache[pdf]
    r = subprocess.run(
        ['pdftotext', '-bbox-layout', FONTE + pdf, '-'],
        capture_output=True,
    )
    xml = r.stdout.decode('utf-8', 'replace')
    partes = [
        (m.start(), m.end()) for m in layout.PAGE_RE.finditer(xml)
    ]
    paginas = []
    for i, (ini, _fim) in enumerate(partes, 1):
        fim_txt = partes[i][0] if i + 1 < len(partes) else len(xml)
        trecho = xml[ini:fim_txt]
        palavras = [
            (float(w[0]), float(w[1]), float(w[2]), float(w[3]),
             unicodedata.normalize('NFC', w[4]))
            for w in layout.WORD_RE.findall(trecho)
        ]
        palavras = [w for w in palavras if w[4].strip()]
        paginas.append((i, palavras))
    _cache[pdf] = paginas
    return paginas


def e_letra_de_alternativa(palavra):
    """-> letra ou None."""
    x0, y0, x1, y1, txt = palavra
    h = y1 - y0
    if not (H_ALTERNATIVA[0] <= h <= H_ALTERNATIVA[1]):
        return None
    if len(txt) == 1 and txt in 'ABCDE':
        return txt
    return None


def sequencias_por_pagina(pdf):
    """-> {pagina: [[(letra, y0, y1, x0), ...], ...]} — colunas x grupos.

    Em página de DUAS colunas, as alternativas das duas questões se
    alternam na ordem vertical (A da esquerda, A da direita, B da esquerda,
    B da direita...). Sem separar por coluna, a sequência A..B..C..D..E não
    fecha. O x resolve: a coluna da esquerda tem x de margem, a da direita,
    x de meio de página.
    """
    saida = {}
    for pag, palavras in geometria(pdf):
        achados = [
            (e_letra_de_alternativa(p), p[1], p[3], p[0])
            for p in palavras
            if e_letra_de_alternativa(p)
        ]
        if not achados:
            continue
        # separa por CLUSTER de x: as alternativas de uma questão ficam todas
        # na mesma margem (52 pt ou 321 pt), colunas diferentes distam mais de
        # 100 pt. Agrupar por ">x_min+40" erraria porque o texto da alternativa
        # alarga a caixa do bloco, não a da letra.
        xs = sorted({a[3] for a in achados})
        grupos_x = [[xs[0]]]
        for x in xs[1:]:
            if x - grupos_x[-1][-1] > 100:
                grupos_x.append([x])
            else:
                grupos_x[-1].append(x)
        if len(grupos_x) == 1:
            colunas = [achados]
        else:
            colunas = []
            for gx in grupos_x:
                alvo = gx[0]
                colunas.append([a for a in achados if abs(a[3] - alvo) < 50])
        # Duas questões na mesma margem ficam em sequência no texto; o
        # indice_por_pagina quebra os blocos pela letra A, então não precisa
        # separar aqui.
        for grupo in colunas:
            grupo.sort(key=lambda a: (a[1], a[3]))
            saida.setdefault(pag, []).append(grupo)
    return saida


def indice_por_pagina(pdf):
    """-> {pagina: [[(letra, y0, y1, x0), ...], ...]} — um grupo por questão.

    Uma página pode ter duas ou três questões, então o valor é uma LISTA de
    grupos. Só entram grupos que formam a sequência A..B..(C..D..E): uma
    letra solta no meio do enunciado não é alternativa.
    """
    por_pag = sequencias_por_pagina(pdf)
    grupos = {}
    for pag, colunas in sorted(por_pag.items()):
        for achados in colunas:
            i = 0
            while i < len(achados):
                letra = achados[i][0]
                if letra != 'A':
                    i += 1
                    continue
                # procura B..E logo abaixo
                esperado = 'B'
                grupo = [achados[i]]
                k = i + 1
                while k < len(achados) and esperado <= 'E':
                    if achados[k][0] == esperado and achados[k][1] - grupo[-1][2] < 40:
                        grupo.append(achados[k])
                        esperado = chr(ord(esperado) + 1)
                    k += 1
                # 4 ou 5: o INEP às vezes usa só A..D (pergunta de alternativa
                # múltipla com 4 opções) e o gabarito confirma o resto.
                if len(grupo) >= 4:
                    grupos.setdefault(pag, []).append(grupo)
                    i = k
                else:
                    i += 1
    return grupos


if __name__ == '__main__':
    import ocr

    for arq in ('2014-e1_prova.pdf', '2017-e1_prova.pdf'):
        g = indice_por_pagina(arq)
        print('=' * 12, arq, '->', sum(len(v) for v in g.values()) // 5, 'questoes com alternativas')
        for pag, lista in list(g.items())[:3]:
            for grupo in lista:
                print(f'   p{pag}: ' + ' '.join(a[0] for a in grupo))