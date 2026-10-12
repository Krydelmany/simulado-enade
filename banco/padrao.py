"""Extrai o PADRÃO DE RESPOSTA das questões discursivas.

Os PDFs do INEP têm duas formas:

- **2014/2017/2023**: o arquivo traz enunciado E padrão lado a lado. O padrão
  vem depois de um cabeçalho ("PADRÃO RESPOSTA", "Padrão de Resposta"), até a
  questão seguinte.
- **2019**: o arquivo traz SÓ os padrões, um por discursiva, na ordem D1..D5.
  Cada um começa num cabeçalho de padrão.

Nos dois casos o recorte é pelo cabeçalho — o que importa é não deixar o
próximo enunciado vazar para dentro do padrão anterior.
"""

import re
import sys

sys.path.insert(0, '/root/enade-simulado/banco')
import layout
import parser as _parser

FONTE = '/root/enade-simulado/fontes/'
PADRAO = {
    2014: '2014-e3_padrao.pdf',
    2017: '2017-e3_padrao.pdf',
    2019: '2019-e3_padrao.pdf',
    2023: '2023-padrao.pdf',
}

CAB_PADRAO = re.compile(
    # o INEP escreve de três formas: "PADRÃO DE RESPOSTA", "Padrão de
    # Resposta:" e "Padrão de respostas" (plural) — e a acentuação chega
    # quebrada em alguns arquivos, então o acento é opcional.
    r'^\s*(?:'
    r'PADR[A\u00c3\u00a3]O\s+(?:DE\s+)?RESPOSTAS?'
    r'(?:\s*[-\u2013\u2014]\s*ELABORAD\w*)?'
    r'|Padr(?:es|\u00e3o|\u00e3o)?\s+(?:de\s+)?[Rr]espostas?:?'
    r')\s*$',
    re.I,
)

# título do próximo enunciado: fecha o padrão anterior
INICIO_QUESTAO = re.compile(
    r'^\s*QUEST[ÃA]O\s+(?:(?:DISCURSIVA)\s+)?\d{1,2}\s*$', re.I
)

LIXO = re.compile(
    r'^\s*(?:\d{0,3}\s*ENGENHARIA DE COMPUTA[ÇC][ÃA]O\s*\d{0,3}|[ÁA]REA\s+LIVRE'
    r'|\d{1,3}|VALIDINEP\d{4}[A-Z0-9]*)\s*$',
    re.I,
)


def texto(ano):
    return layout.normaliza(layout.limpar(layout.texto(FONTE + PADRAO[ano])))


def extrair(ano):
    """-> {qid: padrao_texto}"""
    t = texto(ano)
    linhas = t.split('\n')
    cfg = _parser.EDICOES[ano]

    marcas = [(i, ln) for i, ln in enumerate(linhas) if CAB_PADRAO.match(ln)]
    if not marcas:
        return {}

    # as discursivas do PDF, na ordem em que aparecem
    disc = []
    for ln in linhas:
        m = re.match(r'^\s*QUEST[ÃA]O\s+(DISCURSIVA\s+)?(\d{1,2})\s*$', ln, re.I)
        if m and m.group(1):
            disc.append(int(m.group(2)))
    if not disc:
        disc = list(range(1, len(marcas) + 1))   # 2019: só os padrões

    saida = {}
    for k, (i, _m) in enumerate(marcas):
        fim = _fim_do_bloco(linhas, i, marcas, k)
        corpo = [ln.rstrip() for ln in linhas[i + 1 : fim]]
        limpo = [ln for ln in corpo if not LIXO.match(ln)]
        txt = '\n'.join(limpo).strip()
        if not txt or k >= len(disc):
            continue
        num = disc[k]
        qid = f"{ano}-{_parte(cfg, num)}-D{num:02d}"
        saida[qid] = txt
    return saida


def _parte(cfg, num):
    lo, hi = cfg['fg_d']
    return 'FG' if lo <= num <= hi else 'CE'


def _fim_do_bloco(linhas, inicio, marcas, k):
    """Fim do padrão atual: próxima marca, ou o próximo enunciado."""
    for j in range(inicio + 1, len(linhas)):
        if INICIO_QUESTAO.match(linhas[j]):
            return j
    if k + 1 < len(marcas):
        return marcas[k + 1][0]
    return len(linhas)


if __name__ == '__main__':
    ano = int(sys.argv[1])
    d = extrair(ano)
    for k, v in d.items():
        print('=' * 12, k, len(v), 'chars')
        print(v[:200].replace('\n', ' '))
        print()