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
import qualidade
import montar

RAIZ = '/root/enade-simulado'
BANCO = f'{RAIZ}/app/static/banco'
REVISAO = f'{RAIZ}/revisao'

# Figura/tabela citada no ENUNCIADO: entra como imagem recortada da página.
# O alt descreve o desenho para quem usa leitor de tela — não é decoração.
IMAGENS = {
    '2019-CE-Q11': 'Tabela de conflitos de horário entre os cinco grupos de eventos.',
    '2019-CE-Q12': 'Gráfico da região viável em空间 de duas variáveis, com os pontos A a F.',
    '2019-CE-Q15': 'Tabela com os quatro pontos usados no ajuste de reta por mínimos quadrados.',
    '2019-CE-Q16': 'Diagrama esquemático do demultiplexador de quatro canais com CIs 7404 e 7411.',
    '2019-CE-Q21': 'Tabela com os cinco fornecedores e os critérios CD1 a CD6.',
    '2019-CE-Q23': 'Autômato de estados finitos com os estados P, I1 e I0.',
    '2019-CE-Q24': 'Tabela com o custo de cada enlace da rede.',
    '2019-CE-Q27': 'Diagrama de classes UML do padrão Strategy.',
    '2019-CE-Q31': 'Diagrama dos estados dos processos: execução, espera e pronto.',
    '2019-CE-Q32': 'Tabela com as medidas de temperatura de cada período de monitoramento.',
    '2019-FG-Q02': 'Poema concreto de Augusto de Campos.',
    '2019-FG-D02': 'Diagrama da hélice tríplice: setor público, instituição de ensino superior e empresa.',
    '2019-FG-Q05': 'Duas fotos: uma cava a céu aberto na floresta e um povoado com construções e torres de energia.',
    '2019-FG-Q06': 'Gráfico do Atlas da Violência: homicídios de mulheres negras e não negras.',
    '2019-FG-Q06': 'Gráfico do Atlas da Violência: homicídios de mulheres negras e não negras.',
    '2023-CE-Q10': 'Desenho do cilindro-resistor com os pontos A e L indicados.',
    '2023-CE-Q13': 'Circuito elétrico e o grafo equivalente, com as correntes I1 a I6.',
    '2023-CE-Q22': 'Diagrama do banco de dados relacional com as tabelas pessoa, cliente e funcionario.',
    '2023-CE-Q23': 'Figuras 1 e 2: os dois circuitos que formam os filtros.',
    '2023-CE-Q25': 'Contador assíncrono de quatro bits com quatro flip-flops JK.',
    '2023-CE-Q32': 'Grafo de conexão das cidades e o quadro com as distâncias até São Paulo.',
    '2023-FG-Q03': 'Gráfico das taxas de vacinação infantil de 2017 a 2021.',
    # ---- 2014 ----
    '2014-FG-D01': 'Quadro de mobilidade urbana em cidade com mais de 500 mil habitantes.',
    '2014-FG-Q03': 'Gráfico de barras da razão entre pegada ecológica e biocapacidade do planeta.',
    '2014-FG-Q06': 'Gráfico da jornada média semanal de trabalho das mulheres e dos homens no Brasil.',
    '2014-FG-Q07': 'Quadro da proporção de trabalhadores por faixa de deslocamento casa-trabalho.',
    '2014-CE-Q10': 'Circuito com a fonte de 12 V e as lâmpadas L1, L2 e L3.',
    '2014-CE-Q11': 'Quadro de classificação da DBO, imagem do rio com as seções X, Y, Z, W e T, e quadro dos resultados.',
    '2014-CE-Q12': 'Desenho da parede com as camadas e tabela de condutividade térmica dos materiais.',
    '2014-CE-Q14': 'Fluxograma dos dez blocos do sistema.',
    '2014-CE-Q15': 'Listagem do programa de ordenação, com as linhas numeradas.',
    '2014-CE-Q17': 'Gráficos I e II com os candidatos A e B.',
    '2014-CE-Q23': 'Estrutura da matriz lógica programável, dos estágios AND e OR às saídas.',
    '2014-CE-Q24': 'Diagramas de troca de mensagens do protocolo TCP.',
    '2014-CE-Q25': 'Lugar das raízes no plano complexo.',
    '2014-CE-Q26': 'Quadros da rede neural: pesos, entradas e saídas.',
    '2014-CE-Q27': 'Protótipo de tela de classificados no celular.',
    '2014-CE-Q28': 'Diagrama do sistema de aquisição de sinal, do sensor ao conversor.',
    # ---- 2017 ----
    '2017-FG-Q01': 'Gráficos das contribuições para a União Europeia e do Reino Unido e da União Europeia.',
    '2017-FG-Q03': 'Tabela de potência e tempo de uso dos eletrodomésticos.',
    '2017-FG-Q04': 'Tirinha em quatro quadros sobre o tempo de atenção diante da televisão.',
    '2017-FG-Q05': 'Infográfico sobre o que são e para que servem os hidrogéis.',
    '2017-FG-Q08': 'Figura com os Objetivos de Desenvolvimento Sustentável.',
    '2017-CE-Q09': 'Curvas de tensão por corrente de um dispositivo.',
    '2017-CE-D04': 'Termistores NTC e circuito de interface com a resistência de referência.',
    '2017-CE-Q32': 'Diagrama das etapas do pipeline de renderização gráfica.',
    '2017-CE-Q35': 'Grafo de roteadores usado no cálculo do caminho mais curto.',
}

# questões cujas alternativas são desenho (código/fórmula/diagrama): entram
# como imagem recortada da página, não como texto
FIGURAS = {
    '2019-CE-Q09': 'Alternativas A a E: implementação do método sort em Java.',
    '2019-CE-Q14': 'Alternativas A a E: resposta em frequência H(e^jΩ) de cada opção.',
    '2019-CE-Q22': 'Alternativas A a E: diagramas das redes bayesianas candidatas.',
}

LOTE = {
    (2019, 'FG'): 1,
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
    for q in qs:
        alt = IMAGENS.get(q['id'])
        if alt:
            q['imagem'] = {'src': f'/banco/img/{q["id"]}.png', 'alt': alt}
    qs = [q for q in qs if q['parte'] == parte]

    # Porta de qualidade (ver qualidade.py): uma objetiva com alternativa
    # faltando, vazia ou com pedaço de enunciado é PIOR que não existir — o
    # aluno marcaria uma letra e levaria o resultado errado sem perceber.
    boas, pendentes = [], []
    for q in (qualidade.limpa(q) for q in qs):
        motivo = qualidade.problema(q)
        if motivo:
            pendentes.append((q, motivo))
        else:
            boas.append(q)

    ordem = {'discursiva': 0, 'objetiva': 1}
    qs = sorted(boas, key=lambda q: (ordem.get(q['tipo'], 9), q['numero']))

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
    if pendentes:
        L += [
            '',
            f'## ⚠️ {len(pendentes)} questão(ões) FORA do banco',
            '',
            'O extrator não achou as cinco alternativas (o OCR da prova perde a '
            'bolinha em algumas). Não entraram no site porque, com uma '
            'alternativa faltando, o gabarito aponta para a letra errada. '
            'Precisam de digitação manual:',
            '',
        ]
        for q, motivo in pendentes:
            ach = ', '.join(sorted(q.get('alternativas') or {})) or '—'
            gab = q.get('gabarito') or '?'
            L.append(f'- `{q["id"]}` — {motivo} (lidas: {ach}, gabarito {gab})')
        L.append('')
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


def resumo():
    """Lista única do que ainda falta, das quatro edições.

    Os lotes ficam um por arquivo; este junta tudo num só lugar, que é o
    que dá para conferir de uma vez.
    """
    L = ['# Pendências da extração', '',
         'Questões do PDF oficial que **não entraram no banco** porque o '
         'extrator não conseguiu ler as cinco alternativas (o OCR da prova '
         'perde a bolinha). Com alternativa faltando, o gabarito aponta '
         'para a letra errada — por isso ficam de fora em vez de irem '
         'erradas.', '']
    total = entrada = 0
    for ano in (2014, 2017, 2019, 2023):
        # `aplicar_figuras` é o que marca as questões de alternativa-em-imagem
        # (código, fórmula, diagrama): elas não têm texto para conferir, e
        # por isso não são pendência
        qs = montar.aplicar_figuras(
            classificar.aplicar(montar.extrair(ano)), FIGURAS
        )
        qs = [qualidade.limpa(q) for q in qs]
        ok = [q for q in qs if not qualidade.problema(q)]
        bad = [(q, qualidade.problema(q)) for q in qs if qualidade.problema(q)]
        entrada += len(ok)
        total += len(qs)
        L.append(f'## {ano} — {len(ok)} de {len(qs)} no banco')
        if bad:
            L.append('')
            for q, motivo in bad:
                gab = q.get('gabarito') or '?'
                L.append(f'- `{q["id"]}` ({q["parte"]}) — {motivo}; '
                         f'gabarito {gab}')
        L.append('')
    L.insert(3, f'**{entrada} questões no banco** de {total} extraídas '
                f'({total - entrada} pendentes).')
    L += ['', '---', '',
          'Para fechar uma pendência: abrir o PDF da edição, digitar as '
          'cinco alternativas e pôr no `classificacao.json`/no gerador. O '
          'gabarito vem do PDF de gabaritos, então só ele não basta — '
          'sem as cinco opções a questão não pode ir ao site.', '']
    os.makedirs(REVISAO, exist_ok=True)
    with open(f'{REVISAO}/pendencias.md', 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L))
    print(f'{entrada}/{total} no banco -> {REVISAO}/pendencias.md')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'resumo':
        resumo()
    else:
        main(int(sys.argv[1]), sys.argv[2])
