"""Renderiza a faixa de uma questão para leitura humana.

    python3 banco/olho.py 2017-CE-Q11 [--dpi 400]

O OCR de 2014/2017 erra justamente o que dá para ler de olho — a bolinha da
alternativa e o bloco de opções quando a coluna quebra. Em vez de adivinhar,
este comando entrega a imagem recortada da questão; quem (ou o que) lê a
imagem digita as alternativas em `digitadas.json`, e o pipeline entra com
elas antes da porta de qualidade — do mesmo jeito que `montar.CORRECOES` já
fazia para a 2023-CE-Q18.

Saída em `revisao/img/<qid>.png`, em pontos do PDF escalados para `--dpi`.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import figura  # noqa: E402

SAIDA = '/root/enade-simulado/revisao/img'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('qid')
    ap.add_argument('--dpi', type=int, default=400)
    ap.add_argument('--so-alternativas', action='store_true',
                    help='corta a partir da última linha do enunciado — '
                         'útil quando o que falta é só o bloco de opções')
    a = ap.parse_args()

    edicao = int(a.qid[:4])
    achado = figura.achar_pagina(
        figura.PROVAS_PATH + str(edicao) + '-e1_prova.pdf', edicao, a.qid
    )
    if achado is None:
        raise SystemExit(f'página de {a.qid} não encontrada')
    pag, y_ini, W, H, ls = achado
    topo, base = figura.limites(ls, y_ini, H, W)
    print(f'{a.qid}: página {pag}, faixa y {topo:.0f}–{base:.0f} de {H:.0f}pt')

    os.makedirs(SAIDA, exist_ok=True)
    destino = f'{SAIDA}/{a.qid}.png'
    _, tam = figura.figura(
        figura.PROVAS_PATH + str(edicao) + '-e1_prova.pdf', edicao, a.qid,
        destino, y_topo=topo - 6, y_base=base - 4, dpi=a.dpi
    )
    print(f'{destino} — {tam[0]}x{tam[1]}px')


if __name__ == '__main__':
    main()
