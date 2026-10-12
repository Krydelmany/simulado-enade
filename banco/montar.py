"""Monta o rascunho do banco (JSON) a partir do texto de uma prova.

Gera a estrutura com enunciado/alternativas/gabarito; `tema`, `dificuldade`
e `materia_ava` entram depois, na revisão (ver revisao/).
"""

import json
import os
import re
import sys

sys.path.insert(0, '/root/enade-simulado/banco')
import layout
import parser

FONTE = '/root/enade-simulado/fontes/'
PROVAS = {
    2014: '2014-e1_prova.pdf',
    2017: '2017-e1_prova.pdf',
    2019: '2019-e1_prova.pdf',
    2023: '2023-prova.pdf',
}
GABARITO = {
    2014: '2014-e2_gabarito.txt',
    2017: '2017-e2_gabarito.txt',
    2019: '2019-e2_gabarito.txt',
    2023: '2023-gabarito.txt',
}


def gabaritos(ano):
    """-> {numero(int): letra|'ANULADA'}"""
    txt = open(FONTE + GABARITO[ano], encoding='utf-8').read()
    out = {}
    for m in re.finditer(r'QUEST[ÃA]O\s+(\d{1,2})\s+([A-E]|ANULADA)', txt, re.I):
        out[int(m.group(1))] = m.group(2).upper()
    return out


CACHE = '/tmp/opencode/extr'


def texto_da_prova(ano, cache=None):
    """2014/2017 têm fonte quebrada -> usa o OCR (ver ocr.py).

    2019 e 2023 têm texto íntegro: extrai na hora e guarda em cache, para
    não reprocessar o PDF a cada geração de lote.
    """
    ocr = f'{CACHE}/ocr/{ano}-ocr.txt'
    if os.path.exists(ocr):
        with open(ocr, encoding='utf-8') as fh:
            return fh.read()
    cache_txt = f'{CACHE}/{ano}-stext.txt'
    if cache_txt and os.path.exists(cache_txt):
        with open(cache_txt, encoding='utf-8') as fh:
            return fh.read()
    txt = layout.normaliza(layout.limpar(layout.texto(FONTE + PROVAS[ano])))
    with open(cache_txt, 'w', encoding='utf-8') as fh:
        fh.write(txt)
    return txt


def extrair(ano):
    txt = texto_da_prova(ano)
    gab = gabaritos(ano)
    out = []
    for idx, tipo, num, parte, corpo in parser.cortar(txt, ano):
        if tipo == 'objetiva':
            en, alt = parser.separar_alternativas(corpo)
        else:
            en, alt = corpo.strip(), {}
        q = {
            'id': f'{ano}-{parte}-{"D" if tipo == "discursiva" else "Q"}{num:02d}',
            'edicao': ano,
            'parte': parte,
            'numero': f'{num:02d}',
            'tipo': tipo,
            'tema': '',
            'dificuldade': '',
            'figura': None,
            'enunciado': parser.limpar_texto(en),
            'alternativas': {k: parser.limpar_texto(v) for k, v in parser.juntar(alt)},
        }
        if tipo == 'objetiva':
            q['gabarito'] = gab.get(num, '')
        else:
            q['padrao'] = ''
        q['materia_ava'] = None
        out.append(q)
    return out


# Diagrama vira "MDAD / TLMA / A / MDAD / TLMA / B…" no texto extraído: os
# nós e as letras sobram depois que o desenho virou imagem. Estes cortes vão por
# questão porque cada enunciado termina num fraseado diferente.
CORTE_FIM = {
    '2019-CE-Q22': 'Assim, a rede bayesiana para esse domínio é',
    '2019-CE-Q09': 'a implementação do protótpio do método sort da classe MergeSort é',
    '2019-CE-Q14': 'que atenda essas especificações é',
}


def aplicar_figuras(qs, fig_map):
    """Troca as alternativas visuais (código/fórmula/diagrama) por imagem.

    Questão cujas alternativas são desenho não cabe em texto: o gabarito
    continua valendo e a imagem entra no lugar da lista. Também corta do
    enunciado os restos do desenho.
    """
    import re as _re
    for q in qs:
        f = fig_map.get(q['id'])
        if not f:
            continue
        marca = CORTE_FIM.get(q['id'])
        if marca:
            # o texto vem com quebras de linha do PDF; compara sem elas
            alvo = ' '.join(q['enunciado'].split())
            achado = alvo.find(marca)
            if achado >= 0:
                q['enunciado'] = (
                    ' '.join(alvo[: achado + len(marca)].split())
                    + ' (ver as alternativas na imagem).'
                ).strip()
        q['alternativas'] = {}
        q['imagem'] = {
            'src': f'/banco/img/{q["id"]}.png',
            'alt': f,
        }
        q['alternativas_visuais'] = True
    return qs


if __name__ == '__main__':
    ano = int(sys.argv[1])
    qs = extrair(ano)
    print(json.dumps(qs, ensure_ascii=False, indent=1)[:1500])
    print('...total', len(qs))
