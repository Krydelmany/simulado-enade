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

# linguagens que o `formato.py` pode marcar — o `TextoRico.svelte` só usa isto
# para escolher a fonte, então qualquer outra string é fence colado na frase
LINGUAGENS = {'c', 'java', 'python', 'sql', 'vhdl', 'html', 'xml', 'text'}


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

    problemas = []
    vistos = set()
    total = 0

    for arq in arquivos:
        for q in json.load(open(arq, encoding='utf-8')):
            total += 1
            nome = os.path.basename(arq)
            qid = q.get('id', '(sem id)')

            if qid in vistos:
                problemas.append((nome, qid, 'id duplicado'))
            vistos.add(qid)

            for campo in ('edicao', 'parte', 'numero', 'tipo', 'tema', 'enunciado'):
                if not q.get(campo):
                    problemas.append((nome, qid, f'sem {campo}'))

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
            if LIXO.search(enunciado) or CABECALHO.search(enunciado):
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
    if not problemas:
        print('OK — nenhum problema encontrado')
        return 0

    print(f'\n{len(problemas)} problema(s):')
    for nome, qid, msg in problemas:
        print(f'  {nome:26s} {qid:14s} {msg}')
    return 1


if __name__ == '__main__':
    sys.exit(main())