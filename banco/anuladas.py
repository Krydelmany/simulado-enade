"""Questões ANULADAS pelo INEP: saem do banco do site.

Uma questão anulada não tem letra certa: no treino, qualquer letra dava
acerto, então ela não ensinava nada. Ela fica guardada à parte em
`banco/anuladas.json`, que fica fora de `app/static` e o site não carrega.
Só a anulação conta: discursiva com padrão sem texto (`padrao_placeholder`)
continua no banco.

A separação é automática: `gerar.py` e `digita.py --banco` chamam
`separar_banco()` antes de terminar, então uma anulada que volte à
`enade*.json` (reextração, `_nova` em `digitadas.json`) sai de novo para o
mesmo lugar. O `validar.py` reprova se sobrar alguma no banco do site.

    python3 banco/anuladas.py        # separa as que estiverem no banco
"""

import glob
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANCO = os.path.join(RAIZ, 'app', 'static', 'banco')
ARQUIVO = os.path.join(RAIZ, 'banco', 'anuladas.json')


def anulada(q):
    """A questão foi anulada pelo INEP (gabarito oficial "ANULADA")?"""
    return (q.get('gabarito') or '').strip() == 'ANULADA'


def carregar():
    """-> lista de `anuladas.json` (vazia se o arquivo não existe)."""
    if not os.path.exists(ARQUIVO):
        return []
    with open(ARQUIVO, encoding='utf-8') as fh:
        return json.load(fh)


def separar(qs):
    """-> (as que ficam no banco, as anuladas)."""
    ficam = [q for q in qs if not anulada(q)]
    return ficam, [q for q in qs if anulada(q)]


def guardar(novas):
    """Junta `novas` a `anuladas.json`, por id (a versão nova substitui)."""
    if not novas:
        return
    por_id = {q['id']: q for q in carregar()}
    for q in novas:
        por_id[q['id']] = q
    with open(ARQUIVO, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(sorted(por_id.values(), key=lambda q: q['id']), fh,
                  ensure_ascii=False, indent=1)
        fh.write('\n')


def separar_banco():
    """Tira dos `enade*.json` do site as questões anuladas."""
    arquivos = {}
    novas = []
    for arq in sorted(glob.glob(os.path.join(BANCO, 'enade*.json'))):
        with open(arq, encoding='utf-8') as fh:
            qs = json.load(fh)
        ficam, anuladas = separar(qs)
        if anuladas:
            arquivos[arq] = ficam
            novas += anuladas
    # grava `anuladas.json` ANTES de encurtar o banco: se algo der errado no
    # meio, a questão fica duplicada (o validar.py acusa), nunca perdida
    guardar(novas)
    for arq, ficam in arquivos.items():
        with open(arq, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(ficam, fh, ensure_ascii=False, indent=1)
            fh.write('\n')
    for q in novas:
        print(f'  - {q["id"]} -> anuladas.json')
    print(f'{len(novas)} anuladas separadas; {len(carregar())} em anuladas.json')
    return 0


if __name__ == '__main__':
    sys.exit(separar_banco())
