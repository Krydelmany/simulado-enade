"""Aplica tema / dificuldade / materia às questões extraídas.

A fonte da verdade é `classificacao.json` (id -> [tema, dificuldade, materia])
— um arquivo separado para não ter dado dentro de código, e para dar para
revisar/editar as classificações sem mexer em Python.

`materia` é o id de uma matéria de `app/src/lib/materias.json`: as 20 áreas
do Componente Específico da Portaria INEP nº 161/2026 (CE) ou uma das
matérias de Formação Geral herdadas do AVA. A taxonomia mora no app porque o
site precisa dela para os nomes; aqui ela só é lida para recusar id torto —
uma matéria que não existe na lista some do filtro sem aviso nenhum.

    python3 banco/classificar.py 2019     # confere a classificação de uma prova
    python3 banco/classificar.py --banco  # reaplica no banco do site, sem PDF
"""

import glob
import json
import os
import sys

sys.path.insert(0, '/root/enade-simulado/banco')

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
ARQUIVO = os.path.join(AQUI, 'classificacao.json')
TAXONOMIA = os.path.join(RAIZ, 'app', 'src', 'lib', 'materias.json')
BANCO = os.path.join(RAIZ, 'app', 'static', 'banco')

with open(ARQUIVO, encoding='utf-8') as fh:
    _BRUTO = json.load(fh)

CLASSIF = {k: tuple(v) for k, v in _BRUTO.items()}


def materias():
    """-> set com os ids de matéria válidos (CE + FG)."""
    with open(TAXONOMIA, encoding='utf-8') as fh:
        tax = json.load(fh)
    return {m['id'] for m in tax['ce'] + tax['fg']}


def aplicar(qs):
    for q in qs:
        c = CLASSIF.get(q['id'])
        if c:
            q['tema'], q['dificuldade'], q['materia'] = c
        # campo antigo: a matéria do AVA virou `materia` (ver materias.json)
        q.pop('materia_ava', None)
    return qs


def sem_classificar(qs):
    return [q['id'] for q in qs if not q.get('tema')]


def materia_invalida():
    """-> ids de classificacao.json cuja matéria não está na taxonomia."""
    validas = materias()
    return [k for k, v in CLASSIF.items() if v[2] not in validas]


def reaplicar_banco():
    """Reescreve `tema/dificuldade/materia` nos JSON do site a partir de
    `classificacao.json`, sem passar pela extração.

    Existe porque a extração precisa dos PDFs, do poppler e do tesseract —
    e mudar a matéria de uma questão não deveria exigir nada disso. O resto
    da questão (enunciado, alternativas, gabarito) não é tocado.
    """
    ruins = materia_invalida()
    if ruins:
        print('matéria fora da taxonomia:', ', '.join(ruins))
        return 1
    for arq in sorted(glob.glob(os.path.join(BANCO, 'enade*.json'))):
        with open(arq, encoding='utf-8') as fh:
            qs = json.load(fh)
        aplicar(qs)
        with open(arq, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(qs, fh, ensure_ascii=False, indent=1)
            fh.write('\n')
        faltando = [q['id'] for q in qs if not q.get('materia')]
        print(f'{os.path.basename(arq)}: {len(qs)} questões'
              + (f' — SEM matéria: {", ".join(faltando)}' if faltando else ''))
    return 0


if __name__ == '__main__':
    if '--banco' in sys.argv:
        sys.exit(reaplicar_banco())

    import montar

    ano = int(sys.argv[1])
    qs = aplicar(montar.extrair(ano))
    faltando = sem_classificar(qs)
    print(f'{ano}: {len(qs)} questões, {len(CLASSIF)} classificações no arquivo')
    if faltando:
        print('sem classificação:', ', '.join(faltando))
    else:
        print('todas classificadas')
    ruins = materia_invalida()
    if ruins:
        print('matéria fora da taxonomia:', ', '.join(ruins))
