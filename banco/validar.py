"""Validação do banco gerado — roda fora do build, mas deveria rodar dentro.

Cada regra aqui já aconteceu de verdade: alternativa repetida, enunciado
vazado para dentro da alternativa, `padrao` que é placeholder, imagem que não
existe no disco. Nenhuma delas dá erro em runtime — a página abre, a questão
aparece e o aluno responde errado sem perceber que o problema era o dado.

    python3 banco/validar.py          # sai com 1 se algo estiver errado
"""

import glob
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANCO = os.path.join(RAIZ, 'app', 'static', 'banco')
IMG = os.path.join(BANCO, 'img')
TAXONOMIA = os.path.join(RAIZ, 'app', 'src', 'lib', 'materias.json')

# vocabulário do campo `dificuldade` (o mesmo das oficiais); o Estudo usa os
# três como níveis das questões GERADAS
DIFICULDADES = {'Fácil', 'Média', 'Difícil'}

# `enade` minúsculo É conteúdo legítimo ("a função enade recebe uma lista"),
# então a prova do cabeçalho vai separada e case-sensitive: o `re.I` do resto
# do padrão contaminaria o teste de caixa.
CABECALHO = re.compile(r'\bENADE\b')

LIXO = re.compile(
    r'EN[GW]?ENHARIA\s+(?:DE|N[DE])|Exame\s+Nacional'
    r'|COMPONENTE\s+ESPEC|CADERNOS?\s+DE|FORMA[ÇC][ÃA]O\s+GERAL'
    r'|RASCUNHO|\bLetra\s+L\b|�|/%|de\s+Desempenho\s+de\s+Desempenho',
    re.I,
)

# linguagens que o `formato.py` pode marcar, mais as dos blocos lidos do PDF em
# `digitadas.json` (cpp, haskell, verilog) — o `TextoRico.svelte` só usa isto
# para escolher a fonte, então qualquer outra string é fence colado na frase
LINGUAGENS = {'c', 'cpp', 'java', 'python', 'sql', 'vhdl', 'verilog', 'haskell',
              'html', 'xml', 'text'}


# O mesmo regex do `TextoRico.svelte`. Tem que ser IDÊNTICO ao renderizador:
# a validação só vale se olhar exatamente o que o navegador vai olhar.
FENCE_RENDER = re.compile(r'```([^\n`]*)\n?([\s\S]*?)```')


def checa_blocos(nome, qid, campo, txt, problemas):
    """Todo ``` tem que entrar num bloco, e a linguagem tem que ser conhecida.

    O renderizador casa ```` ```lang … ``` ```` a partir da primeira occurrence
    e segue. Se sobrar ``` por fora, é fence torto — e fence torto não dá
    aviso: o `TextoRico` simplesmente mostra o ``` como texto e perde o
    pedaço de código junto. Foi assim que `…no vetor a[lo..hi].```SEDGEWICK`
    sumiu da tela sem erro nenhum no build.

    Além disso, a "linguagem" é o resto da linha depois do ``` de abertura, sem
    limite de tamanho: se for uma frase, o fence está colado no texto.
    """
    if not txt or '```' not in txt:
        return

    usados = [m.span() for m in FENCE_RENDER.finditer(txt)]
    for m in FENCE_RENDER.finditer(txt):
        lang = m.group(1).strip()
        if lang and lang not in LINGUAGENS:
            problemas.append((
                nome, qid,
                f'{campo} com bloco de código de linguagem desconhecida '
                f'"{lang[:34]}" — o ``` está colado no texto'
            ))
    # cada bloco casa DOIS ``` (abre e fecha). Sobrar um significa bloco sem
    # par — o `TextoRico` não renderiza nada e deixa o ``` solto como texto.
    soltos = txt.count('```') - 2 * len(usados)
    if soltos:
        problemas.append((
            nome, qid,
            f'{campo} com {soltos} ``` fora de um bloco — o código deste '
            'trecho não vai aparecer na tela'
        ))


def main():
    arquivos = sorted(glob.glob(os.path.join(BANCO, 'enade*.json')))
    if not arquivos:
        print('nenhum JSON de banco encontrado')
        return 1
    arquivos += sorted(glob.glob(os.path.join(BANCO, 'geradas*.json')))

    tax = json.load(open(TAXONOMIA, encoding='utf-8'))
    materias_ce = {m['id'] for m in tax['ce']}
    materias = materias_ce | {m['id'] for m in tax['fg']}

    problemas = []
    vistos = set()
    total = 0
    # anuladas ficam fora do site (ver anuladas.py); o mesmo id nos dois
    # lugares quer dizer que a separação parou no meio
    anuladas = set()
    arq_anuladas = os.path.join(RAIZ, 'banco', 'anuladas.json')
    if os.path.exists(arq_anuladas):
        anuladas = {q['id'] for q in json.load(open(arq_anuladas, encoding='utf-8'))}
    digitadas = os.path.join(RAIZ, 'banco', 'digitadas.json')
    lidos_do_pdf = set()
    if os.path.exists(digitadas):
        lidos_do_pdf = {k for k, v in json.load(open(digitadas, encoding='utf-8')).items()
                        if isinstance(v, dict) and v.get('_enunciado')}
    # (materia, dificuldade) -> n, e letra -> n, só das geradas: o Estudo
    # promete os três níveis em toda matéria, e um gabarito concentrado numa
    # letra ensina o aluno a chutar, não a matéria
    cobertura = {}
    letras = {}

    for arq in arquivos:
        for q in json.load(open(arq, encoding='utf-8')):
            total += 1
            nome = os.path.basename(arq)
            qid = q.get('id', '(sem id)')
            gerada = q.get('fonte') == 'gerada'

            if qid in vistos:
                problemas.append((nome, qid, 'id duplicado'))
            vistos.add(qid)
            if qid in anuladas:
                problemas.append((nome, qid, 'também está em anuladas.json'))
            if (q.get('gabarito') or '').strip() == 'ANULADA':
                problemas.append((
                    nome, qid,
                    'anulada no banco do site — rode python banco/anuladas.py'
                ))

            # gerada não tem edição: não saiu de prova nenhuma
            obrigatorios = ('parte', 'numero', 'tipo', 'tema', 'enunciado', 'materia')
            if not gerada:
                obrigatorios = ('edicao',) + obrigatorios
            for campo in obrigatorios:
                if not q.get(campo):
                    problemas.append((nome, qid, f'sem {campo}'))

            if q.get('materia') and q['materia'] not in materias:
                problemas.append((
                    nome, qid,
                    f'matéria "{q["materia"]}" fora de materias.json — a questão '
                    'some do filtro'
                ))

            if gerada:
                if q.get('materia') not in materias_ce:
                    problemas.append((nome, qid, 'gerada fora das 20 áreas do CE'))
                if q.get('dificuldade') not in DIFICULDADES:
                    problemas.append((
                        nome, qid,
                        f'gerada com dificuldade "{q.get("dificuldade")}" — não '
                        'aparece em nível nenhum do Estudo'
                    ))
                if q.get('tipo') != 'objetiva' or not (q.get('gabarito') or '').strip():
                    problemas.append((nome, qid, 'gerada precisa ser objetiva com gabarito'))
                chave = (q.get('materia'), q.get('dificuldade'))
                cobertura[chave] = cobertura.get(chave, 0) + 1
                g = q.get('gabarito')
                letras[g] = letras.get(g, 0) + 1

            checa_blocos(nome, qid, 'enunciado', q.get('enunciado'), problemas)
            checa_blocos(nome, qid, 'padrão', q.get('padrao'), problemas)
            for letra, alt in (q.get('alternativas') or {}).items():
                checa_blocos(nome, qid, f'alternativa {letra}', alt, problemas)

            if q['tipo'] == 'objetiva':
                alt = q.get('alternativas') or {}
                if q.get('alternativas_visuais'):
                    if not q.get('imagem'):
                        problemas.append((
                            nome, qid,
                            'alternativa-em-imagem sem imagem — a questão fica '
                            'sem botão nenhum'
                        ))
                else:
                    if len(alt) != 5:
                        problemas.append((nome, qid, f'{len(alt)} de 5 alternativas'))
                    vals = [v.strip() for v in alt.values() if v and v.strip()]
                    if len(vals) != len(set(vals)):
                        problemas.append((
                            nome, qid, 'alternativas repetidas — o acerto vira sorteio'
                        ))
                    for letra, txt in alt.items():
                        # lixo de página só existe no que veio de PDF
                        if gerada:
                            continue
                        if LIXO.search(txt or '') or CABECALHO.search(txt or ''):
                            problemas.append((
                                nome, qid, f'alternativa {letra} com lixo da página'
                            ))
                    gab = (q.get('gabarito') or '').strip()
                    if gab and gab != 'ANULADA' and gab not in alt:
                        problemas.append((nome, qid, f'gabarito {gab} fora das alternativas'))
            else:
                if not (q.get('padrao') or '').strip() and not q.get('padrao_placeholder'):
                    problemas.append((nome, qid, 'discursiva sem padrão de resposta'))
                elif (
                    len(q.get('padrao') or '') < 300
                    and not q.get('padrao_placeholder')
                ):
                    # padrao curto = remissão a desenho ("o estudante deve
                    # apresentar um desenho tal como:"). Válido, desde que a
                    # questão esteja marcada para a UI não mandar o aluno se
                    # autoavaliar contra o vazio.
                    problemas.append((
                        nome, qid,
                        f'padrão de resposta curto ({len(q["padrao"])} car.) e '
                        'sem a marca padrao_placeholder — a autoavaliação vai '
                        'comparar com um texto vazio'
                    ))

            enunciado = q.get('enunciado') or ''
            # texto lido da imagem do PDF (digitadas.json) não é lixo de
            # página: "na área de Engenharia de Computação" é frase de verdade
            lido = qid in lidos_do_pdf
            if not gerada and not lido and (LIXO.search(enunciado) or CABECALHO.search(enunciado)):
                problemas.append((nome, qid, 'enunciado com lixo da página'))

            img = q.get('imagem')
            if img:
                # o `src` começa com "/" (é URL do site, não caminho do disco),
                # então não dá para juntar com `static` direto
                rel = img['src'].lstrip('/')
                if not rel.startswith('banco/'):
                    problemas.append((nome, qid, f"src fora de /banco/: {img['src']}"))
                elif not os.path.exists(os.path.join(RAIZ, 'app', 'static', rel)):
                    problemas.append((nome, qid, f'imagem não existe: {img["src"]}'))

    print(f'{total} questões em {len(arquivos)} arquivos')

    # resoluções (arquivo à parte do site): batem com o banco e com a fonte?
    import resolucoes
    saida, probs = resolucoes.montar()
    problemas += probs
    if not probs and saida != resolucoes.atual():
        problemas.append((
            'resolucoes.json', '-',
            'desatualizado em relação a banco/resolucoes/ — rode python banco/resolucoes.py'
        ))
    print(f'resoluções: {len(saida)} de {total} questões')
    if cobertura:
        for m in sorted(materias_ce):
            for d in sorted(DIFICULDADES):
                if not cobertura.get((m, d)):
                    problemas.append(('geradas', m, f'nenhuma gerada {d}'))
        n = sum(letras.values())
        print('gabaritos das geradas: ' + ', '.join(
            f'{k} {v}' for k, v in sorted(letras.items())))
        for k, v in letras.items():
            # 5 letras = 20% cada; acima de 30% o chute já compensa
            if n >= 25 and v / n > 0.30:
                problemas.append((
                    'geradas', k, f'{v} de {n} gabaritos na mesma letra'
                ))
    if not problemas:
        print('OK — nenhum problema encontrado')
        return 0

    print(f'\n{len(problemas)} problema(s):')
    for nome, qid, msg in problemas:
        print(f'  {nome:26s} {qid:14s} {msg}')
    return 1


if __name__ == '__main__':
    sys.exit(main())