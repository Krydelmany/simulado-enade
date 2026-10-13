"""Monta o banco de questões GERADAS para revisão (níveis Fácil/Médio/Difícil).

    python3 banco/geradas.py

Lê `banco/geradas/*.json` — um arquivo por matéria do CE — e escreve:

- `app/static/banco/geradas.json`: o que o site carrega, no mesmo formato
  das questões extraídas das provas (id, parte, numero, tipo, tema,
  dificuldade, enunciado, alternativas, gabarito, materia) mais
  `fonte: "gerada"`, que é o que separa as duas no app;
- `revisao/geradas/NN-<materia>.md`: o ponto de conferência humano, igual
  aos lotes das provas. Questão gerada com gabarito errado é tão ruim quanto
  questão oficial com alternativa faltando — o aluno marca a letra certa e
  leva errado sem saber por quê.

O arquivo de origem só tem o que é conteúdo:

    {"materia": "redes", "questoes": [
      {"dificuldade": "Fácil", "tema": "...", "enunciado": "...",
       "alternativas": {"A": "...", ..., "E": "..."}, "gabarito": "D"}, ...]}

O id sai da posição: `GER-<inciso>-<F|M|D><n>` (GER-XVIII-F1 = 1ª fácil de
Redes). Reordenar as questões de um nível dentro do arquivo troca os ids — e
o histórico do aluno é guardado por id —, então questão nova entra no FIM.

Os níveis, para quem escrever mais questões:

- **Fácil**: conceito direto, contexto de uma ou duas frases;
- **Média**: aplicação — um cenário curto e um passo a mais (conta, traço
  de código, escolha entre técnicas);
- **Difícil**: o modelo da prova — situação-problema com texto-base e
  afirmações I/II/III para avaliar, ou asserção-razão (I PORQUE II).
"""

import glob
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
FONTE = os.path.join(AQUI, 'geradas')
SAIDA = os.path.join(RAIZ, 'app', 'static', 'banco', 'geradas.json')
REVISAO = os.path.join(RAIZ, 'revisao', 'geradas')
TAXONOMIA = os.path.join(RAIZ, 'app', 'src', 'lib', 'materias.json')

NIVEL = {'Fácil': 'F', 'Média': 'M', 'Difícil': 'D'}
LETRAS = ('A', 'B', 'C', 'D', 'E')


def carregar_taxonomia():
    with open(TAXONOMIA, encoding='utf-8') as fh:
        return json.load(fh)['ce']


def problemas_da_fonte(q):
    """-> lista de motivos para recusar a questão de origem."""
    p = []
    if q.get('dificuldade') not in NIVEL:
        p.append(f'dificuldade "{q.get("dificuldade")}" (use Fácil/Média/Difícil)')
    for campo in ('tema', 'enunciado'):
        if not (q.get(campo) or '').strip():
            p.append(f'sem {campo}')
    alt = q.get('alternativas') or {}
    if tuple(sorted(alt)) != LETRAS:
        p.append(f'alternativas {sorted(alt)} (precisa A–E)')
    vals = [v.strip() for v in alt.values() if (v or '').strip()]
    if len(vals) != len(set(vals)):
        p.append('alternativas repetidas')
    if q.get('gabarito') not in LETRAS:
        p.append(f'gabarito "{q.get("gabarito")}"')
    return p


def montar():
    """-> (questões prontas, erros, {id da matéria: [questões]})."""
    tax = carregar_taxonomia()
    ordem = {m['id']: i for i, m in enumerate(tax)}
    por_id = {m['id']: m for m in tax}

    saida, erros, por_materia = [], [], {}
    for arq in sorted(glob.glob(os.path.join(FONTE, '*.json'))):
        nome = os.path.basename(arq)
        with open(arq, encoding='utf-8') as fh:
            fonte = json.load(fh)
        mid = fonte.get('materia')
        if mid not in por_id:
            erros.append(f'{nome}: matéria "{mid}" não é uma das 20 do CE')
            continue
        inciso = por_id[mid]['inciso']
        contagem = {}
        for k, q in enumerate(fonte.get('questoes') or [], 1):
            motivos = problemas_da_fonte(q)
            if motivos:
                erros.append(f'{nome} #{k}: ' + '; '.join(motivos))
                continue
            sigla = NIVEL[q['dificuldade']]
            contagem[sigla] = contagem.get(sigla, 0) + 1
            n = contagem[sigla]
            pronta = {
                'id': f'GER-{inciso}-{sigla}{n}',
                'fonte': 'gerada',
                'edicao': None,
                'parte': 'CE',
                'numero': f'{sigla}{n}',
                'tipo': 'objetiva',
                'tema': q['tema'].strip(),
                'dificuldade': q['dificuldade'],
                'figura': None,
                'enunciado': q['enunciado'].strip(),
                'alternativas': {l: q['alternativas'][l].strip() for l in LETRAS},
                'gabarito': q['gabarito'],
                'materia': mid,
            }
            saida.append(pronta)
            por_materia.setdefault(mid, []).append(pronta)

    saida.sort(key=lambda q: (
        ordem[q['materia']], 'FMD'.index(q['numero'][0]), int(q['numero'][1:])
    ))
    return saida, erros, por_materia, tax


def markdown(m, qs):
    L = [
        f'# Geradas — {m["inciso"]}. {m["nome"]} — PARA REVISÃO',
        '',
        f'Área da Portaria INEP nº 161/2026: *{m["oficial"]}*. '
        f'{len(qs)} questões escritas para revisão (não são do INEP). '
        'Confira o gabarito de cada uma; para corrigir, edite '
        f'`banco/geradas/` e rode `python3 banco/geradas.py`.',
        '', '---', '',
    ]
    for q in qs:
        L += [
            f"## {q['id']} — {q['tema']}",
            f"- **Gabarito:** {q['gabarito']}",
            f"- Nível: **{q['dificuldade']}**",
            '',
        ]
        # 4 crases: o enunciado pode ter bloco de código com 3
        L += ['````text', q['enunciado'], '````', '']
        for letra in LETRAS:
            marca = ' ✔' if letra == q['gabarito'] else ''
            L.append(f"{letra}) {q['alternativas'][letra]}{marca}")
        L += ['', '---', '']
    return '\n'.join(L)


def main():
    qs, erros, por_materia, tax = montar()
    if erros:
        print('questões recusadas:')
        for e in erros:
            print('  ' + e)
        return 1

    with open(SAIDA, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(qs, fh, ensure_ascii=False, indent=1)
        fh.write('\n')

    os.makedirs(REVISAO, exist_ok=True)
    for i, m in enumerate(tax, 1):
        if m['id'] not in por_materia:
            continue
        destino = os.path.join(REVISAO, f'{i:02d}-{m["id"]}.md')
        with open(destino, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(markdown(m, por_materia[m['id']]))

    letras = {}
    for q in qs:
        letras[q['gabarito']] = letras.get(q['gabarito'], 0) + 1
    niveis = {}
    for q in qs:
        niveis[q['dificuldade']] = niveis.get(q['dificuldade'], 0) + 1
    print(f'{len(qs)} questões geradas em {len(por_materia)} matérias -> {SAIDA}')
    print('por nível: ' + ', '.join(f'{k} {v}' for k, v in niveis.items()))
    print('gabaritos: ' + ', '.join(f'{k} {v}' for k, v in sorted(letras.items())))
    print('depois: python3 banco/validar.py && python3 banco/versao.py --escrever')
    return 0


if __name__ == '__main__':
    sys.exit(main())
