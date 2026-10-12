"""Aplica tema / dificuldade / materia_ava às questões extraídas.

A fonte da verdade é `classificacao.json` (id -> [tema, dificuldade, materia_ava])
— um arquivo separado para não ter dado dentro de código, e para dar para
revisar/editar as classificações sem mexer em Python.

`tema` segue a taxonomia de 17 áreas que o professor usou no relatório da
turma (ver INVENTARIO.md). `materia_ava` só recebe as disciplinas que existem
de fato no AVA; o resto fica `null` = FG transversal ou sem matéria.
"""

import json
import os
import sys

sys.path.insert(0, '/root/enade-simulado/banco')

ARQUIVO = os.path.join(os.path.dirname(__file__), 'classificacao.json')

with open(ARQUIVO, encoding='utf-8') as fh:
    _BRUTO = json.load(fh)

CLASSIF = {k: tuple(v) for k, v in _BRUTO.items()}


def aplicar(qs):
    for q in qs:
        c = CLASSIF.get(q['id'])
        if c:
            q['tema'], q['dificuldade'], q['materia_ava'] = c
    return qs


def sem_classificar(qs):
    return [q['id'] for q in qs if not q.get('tema')]


if __name__ == '__main__':
    import montar

    ano = int(sys.argv[1])
    qs = aplicar(montar.extrair(ano))
    faltando = sem_classificar(qs)
    print(f'{ano}: {len(qs)} questões, {len(CLASSIF)} classificações no arquivo')
    if faltando:
        print('sem classificação:', ', '.join(faltando))
    else:
        print('todas classificadas')