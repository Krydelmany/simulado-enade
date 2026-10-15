"""Resoluções ("como resolver") das questões: fonte -> arquivo do site.

A fonte editável fica em `banco/resolucoes/`, um arquivo por arquivo do
banco (`enade2019-ce.json`, `geradas.json`…), no formato

    { "<id>": { "texto": "...", "autor": "IA", "auditado": false } }

`autor` e `auditado` são opcionais: sem eles, vale "IA" e não auditado — é o
que a tela mostra no topo do bloco ("IA · Não auditado"). Quem conferir uma
resolução troca `auditado` para true (e o `autor`, se reescreveu).

Este script junta tudo em `app/static/banco/resolucoes.json`, que o site
baixa à parte (ver `app/src/lib/resolucoes.js`), e recusa gravar se algo
não bate com o banco:

 - id que não está no banco (questão que saiu, gerada renumerada);
 - objetiva cuja última linha não é "Resposta: X." com X = gabarito oficial.
   Uma resolução que chega a outra letra ensina errado sem sintoma nenhum;
 - bloco de código torto (a mesma regra do `validar.py`).

    python3 banco/resolucoes.py        # grava o arquivo do site
    python3 banco/resolucoes.py --checar   # só confere (o validar.py usa)
"""

import glob
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANCO = os.path.join(RAIZ, 'app', 'static', 'banco')
FONTE = os.path.join(RAIZ, 'banco', 'resolucoes')
SAIDA = os.path.join(BANCO, 'resolucoes.json')

RESPOSTA = re.compile(r'Resposta: ([A-E])\.?\s*$')


def banco():
    """-> {id: questão} de todos os arquivos que o site carrega."""
    arquivos = sorted(glob.glob(os.path.join(BANCO, 'enade*.json')))
    arquivos += sorted(glob.glob(os.path.join(BANCO, 'geradas*.json')))
    out = {}
    for arq in arquivos:
        with open(arq, encoding='utf-8') as fh:
            for q in json.load(fh):
                out[q['id']] = q
    return out


def montar():
    """-> (resoluções prontas para o site, lista de problemas)."""
    import validar

    questoes = banco()
    saida, problemas = {}, []
    for arq in sorted(glob.glob(os.path.join(FONTE, '*.json'))):
        nome = os.path.basename(arq)
        with open(arq, encoding='utf-8') as fh:
            fonte = json.load(fh)
        for qid, r in fonte.items():
            if qid.startswith('_'):
                continue
            if qid in saida:
                problemas.append((nome, qid, 'resolução repetida em outro arquivo'))
                continue
            q = questoes.get(qid)
            if not q:
                problemas.append((nome, qid, 'questão não está no banco do site'))
                continue
            texto = (r.get('texto') or '').strip() if isinstance(r, dict) else ''
            if not texto:
                problemas.append((nome, qid, 'resolução sem texto'))
                continue
            if q['tipo'] == 'objetiva':
                m = RESPOSTA.search(texto)
                if not m:
                    problemas.append((nome, qid, 'não termina em "Resposta: X."'))
                elif m.group(1) != q.get('gabarito'):
                    problemas.append((
                        nome, qid,
                        f'resolução chega a {m.group(1)}, gabarito oficial é {q.get("gabarito")}'
                    ))
            validar.checa_blocos(nome, qid, 'resolução', texto, problemas)
            autor = r.get('autor') or 'IA'
            auditado = r.get('auditado', False)
            if not isinstance(auditado, bool):
                problemas.append((nome, qid, '"auditado" tem de ser true ou false'))
            saida[qid] = {'texto': texto, 'autor': autor, 'auditado': bool(auditado)}
    return dict(sorted(saida.items())), problemas


def atual():
    """-> o que está hoje no arquivo do site ({} se não existe)."""
    if not os.path.exists(SAIDA):
        return {}
    with open(SAIDA, encoding='utf-8') as fh:
        return json.load(fh)


def main():
    saida, problemas = montar()
    if problemas:
        print('NADA GRAVADO:' if '--checar' not in sys.argv else 'problemas:')
        for nome, qid, msg in problemas:
            print(f'  {nome:22s} {qid:14s} {msg}')
        return 1
    total = len(banco())
    if '--checar' in sys.argv:
        if saida != atual():
            print('resolucoes.json desatualizado — rode python banco/resolucoes.py')
            return 1
        print(f'resoluções: OK {len(saida)} de {total} questões')
        return 0
    with open(SAIDA, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(saida, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    auditadas = sum(1 for r in saida.values() if r['auditado'])
    print(f'{len(saida)} de {total} questões com resolução ({auditadas} auditadas)')
    print('rode python banco/versao.py --escrever')
    return 0


if __name__ == '__main__':
    sys.exit(main())
