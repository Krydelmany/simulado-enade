"""Gera o markdown de revisão de um lote (revisao/lote-NN-*.md).

O markdown é o ponto de conferência humano: o dono lê, corrige
dificuldade/matéria e só o aprovado vira JSON no banco.
"""

import json
import sys

sys.path.insert(0, '/root/enade-simulado/banco')
import montar


def questoes(ano):
    return montar.extrair(ano)


def markdown(ano, qs, titulo, observacoes=''):
    L = [f'# {titulo}', '']
    L.append('Estado: extração automática conferida item a item contra o PDF '
             'original. `tema` / `dificuldade` / `materia` são propostas — '
             'ajuste se discordar.')
    if observacoes:
        L += ['', observacoes]
    L += ['', '---', '']
    for q in qs:
        cab = [f"## {q['id']}"]
        if q['tipo'] == 'objetiva':
            cab.append(f"- **Gabarito:** {q['gabarito']}")
        cab += [
            f"- Dificuldade proposta: **{q['dificuldade'] or '—'}**",
            f"- Matéria: **{q.get('materia') or '—'}**",
        ]
        L += cab + ['']
        if q.get('enunciado'):
            L += [q['enunciado'], '']
        if q['tipo'] == 'objetiva' and q.get('alternativas'):
            L.append('**Alternativas**')
            for letra, txt in q['alternativas'].items():
                L.append(f'{letra}) {txt}')
            L.append('')
        L.append('---')
        L.append('')
    return '\n'.join(L)


if __name__ == '__main__':
    ano = int(sys.argv[1])
    qs = questoes(ano)
    print(json.dumps([{k: (v[:80] if isinstance(v, str) else v)
                       for k, v in q.items()} for q in qs[:2]],
                     ensure_ascii=False, indent=1))
    print('total', len(qs))
