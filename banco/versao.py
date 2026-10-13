"""Reescreve `VERSAO_BANCO` em `app/src/lib/banco.js` a partir do conteúdo.

A cache do banco vive no `sessionStorage` do navegador, com uma versão
embutida no código. Se a versão não muda quando o banco muda, o aluno
continua vendo o banco velho — e foi exatamente o que aconteceu na validação:
o site mostrava 113 questões com o banco já em 112, porque os arquivos tinham
sido regenerados mas a versão era a de antes.

Não dá para editar `banco.js` na mão a cada geração: uma vez esquecida, o
erro é silencioso e dura até o TTL de 6 horas expirar. Então a versão é
derivada do conteúdo — muda junto com o banco, sempre.

    python3 banco/versao.py          # mostra o que faria
    python3 banco/versao.py --escrever
"""

import hashlib
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANCO = os.path.join(RAIZ, 'app', 'static', 'banco')
ALVO = os.path.join(RAIZ, 'app', 'src', 'lib', 'banco.js')

RE_VERSAO = re.compile(r"(export const VERSAO_BANCO = ')([^']*)(')")


def versao():
    """Hash do conteúdo de todos os JSON do banco."""
    h = hashlib.sha256()
    arqs = sorted(f for f in os.listdir(BANCO) if f.endswith('.json'))
    for arq in arqs:
        caminho = os.path.join(BANCO, arq)
        with open(caminho, 'rb') as fh:
            dados = json.load(fh)
        # só o que muda o que o aluno vê: quantas são e os ids
        resumo = [(q.get('id'), q.get('gabarito'), q.get('enunciado')) for q in dados]
        h.update(arq.encode())
        h.update(json.dumps(resumo, ensure_ascii=False, sort_keys=True).encode())
    return h.hexdigest()[:12]


def main():
    v = versao()
    with open(ALVO, encoding='utf-8') as fh:
        src = fh.read()
    atual = RE_VERSAO.search(src)
    if not atual:
        print('VERSAO_BANCO não encontrada em banco.js', file=sys.stderr)
        return 1
    if atual.group(2) == v:
        print(f'versão já atual: {v}')
        return 0
    print(f'{atual.group(2)} -> {v}')
    if '--escrever' not in sys.argv:
        print('rode com --escrever para gravar')
        return 0
    novo = RE_VERSAO.sub(rf"\g<1>{v}\g<3>", src, count=1)
    with open(ALVO, 'w', encoding='utf-8') as fh:
        fh.write(novo)
    print('banco.js atualizado')
    return 0


if __name__ == '__main__':
    sys.exit(main())