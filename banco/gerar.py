"""Gera o JSON do banco + o markdown de revisão de um lote.

    python3 gerar.py 2019 CE

Escreve:
  app/static/banco/enade<ano>-<parte>.json   (entrada do site)
  revisao/lote-NN-<ano>-<parte>.md           (conferência humana)
"""

import json
import os
import sys

sys.path.insert(0, '/root/enade-simulado/banco')
import classificar
import montar

RAIZ = '/root/enade-simulado'
BANCO = f'{RAIZ}/app/static/banco'
REVISAO = f'{RAIZ}/revisao'

# questões cujas alternativas são desenho (código/fórmula/diagrama): entram
# como imagem recortada da página, não como texto
FIGURAS = {
    '2019-CE-Q09': 'Alternativas A a E: implementação do método sort em Java.',
    '2019-CE-Q14': 'Alternativas A a E: resposta em frequência H(e^jΩ) de cada opção.',
    '2019-CE-Q22': 'Alternativas A a E: diagramas das redes bayesianas candidatas.',
}

LOTE = {
    (2019, 'CE'): 2,
    (2023, 'FG'): 3,
    (2023, 'CE'): 4,
    (2014, 'FG'): 5,
    (2014, 'CE'): 6,
    (2017, 'FG'): 7,
    (2017, 'CE'): 8,
}


def parte_nome(parte):
    return {'FG': 'Formação Geral', 'CE': 'Componente Específico'}[parte]


def main(ano, parte):
    qs = classificar.aplicar(montar.extrair(ano))
    qs = montar.aplicar_figuras(qs, FIGURAS)
    qs = [q for q in qs if q['parte'] == parte]

    ordem = {'discursiva': 0, 'objetiva': 1}
    qs.sort(key=lambda q: (ordem.get(q['tipo'], 9), q['numero']))

    # --- JSON do site -------------------------------------------------
    destino = f'{BANCO}/enade{ano}-{parte.lower()}.json'
    with open(destino, 'w', encoding='utf-8') as fh:
        json.dump(qs, fh, ensure_ascii=False, indent=1)
        fh.write('\n')

    # --- markdown de revisão ------------------------------------------
    n = LOTE[(ano, parte)]
    pronto = 'PRONTO' if all(q['tema'] for q in qs) else 'REVISAR CLASSIFICAÇÃO'
    titulo = f'# Lote {n} — ENADE {ano}, {parte_nome(parte)} — {pronto}' 
    L = [titulo, '']
    L.append(
        f'{len(qs)} questão(ões) extraída(s) do PDF oficial do INEP. '
        'Gabarito vem do gabarito definitivo; `tema`, `dificuldade` e '
        '`materia_ava` são propostas — ajuste o que discordar e o banco é '
        'regenerado.'
    )
    sem_tema = [q['id'] for q in qs if not q['tema']]
    if sem_tema:
        L += ['', f'⚠️ **Sem classificação:** {", ".join(sem_tema)}']
    figs = [q for q in qs if q.get('imagem')]
    if figs:
        L += ['', 'Questões com alternativas em imagem (recorte da página): '
                  + ', '.join(q['id'] for q in figs)]
    L += ['', '---', '']

    for q in qs:
        L.append(f"## {q['id']}")
        if q['tipo'] == 'objetiva':
            L.append(f"- **Gabarito:** {q['gabarito'] or '⚠️ não encontrado'}")
        L += [
            f"- Dificuldade proposta: **{q['dificuldade'] or '—'}**",
            f"- Matéria do AVA: **{q['materia_ava'] or '— (FG transversal)'}**",
            '',
        ]
        if q.get('imagem'):
            L += [f"Imagem: `{q['imagem']['src']}` — {q['imagem']['alt']}", '']
        if q['enunciado']:
            L += ['```', q['enunciado'], '```', '']
        if q['tipo'] == 'objetiva' and q.get('alternativas'):
            L.append('**Alternativas**')
            for letra, txt in q['alternativas'].items():
                L.append(f'{letra}) {txt}')
            L.append('')
        L += ['---', '']

    os.makedirs(REVISAO, exist_ok=True)
    md = f'{REVISAO}/lote-{n:02d}-{ano}-{parte}.md'
    with open(md, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L))

    print(f'{len(qs)} questões -> {destino}')
    print(f'                 -> {md}')
    return qs


if __name__ == '__main__':
    main(int(sys.argv[1]), sys.argv[2])
