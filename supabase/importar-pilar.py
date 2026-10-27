#!/usr/bin/env python3
"""Importa o retrato do simulado em papel do pilar.ia.br para o Supabase.

O site do professor (https://pilar.ia.br/enade2026/) guarda o resultado da
prova em papel por RA. O dado é FIXO (não há outro simulado marcado), então
não existe proxy em tempo real: este script roda uma vez, da máquina que tem
rede para o pilar, e gera um SQL que o admin cola no SQL Editor do Supabase.

O SQL faz o de-para pelo RA na tabela `membros` e grava só o resumo (acertos,
percentual, áreas, prioridades e comparação com a turma). Não grava cookie,
resposta por questão nem uma segunda cópia do RA.

Uso:
    python3 supabase/importar-pilar.py --ras /root/.pilar-ras.csv

O CSV pode ter o cabeçalho `ra` (do SQL Editor) ou só uma coluna com um RA
por linha. O SQL sai em /tmp/opencode/desempenho-papel.sql por padrão; os RAs
nunca são impressos no terminal, só mascarados.

Teste sem tocar no pilar de verdade:
    python3 supabase/importar-pilar.py --ras teste.csv --base http://127.0.0.1:8765
"""

import argparse
import csv
import http.cookiejar
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MATERIAS = RAIZ / 'app' / 'src' / 'lib' / 'materias.json'
BASE_PADRAO = 'https://pilar.ia.br/enade2026'
CURSO_PADRAO = 'EngComp'
SQL_PADRAO = Path('/tmp/opencode/desempenho-papel.sql')
TEMPO_LIMITE = 20
PAUSA = 0.4


def normalizar(texto):
    """Minúsculas, sem acento e só letras/números, para comparar nomes."""
    s = unicodedata.normalize('NFD', str(texto or ''))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()


def numero(valor, padrao=None):
    if valor is None or valor == '':
        return padrao
    try:
        return float(valor)
    except (TypeError, ValueError):
        return padrao


def inteiro(valor, padrao=0):
    n = numero(valor, None)
    return padrao if n is None else int(round(n))


def percentual(valor):
    """O pilar usa 0–1; se vier 0–100, normaliza."""
    n = numero(valor, None)
    if n is None:
        return None
    if n > 1:
        n /= 100
    return max(0.0, min(1.0, n))


def sql_texto(valor):
    return "'" + str(valor).replace("'", "''") + "'"


def sql_json(valor):
    return sql_texto(json.dumps(valor, ensure_ascii=False, sort_keys=True)) + '::jsonb'


def sql_num(valor, casas=4):
    if valor is None:
        return 'null'
    return f'{valor:.{casas}f}'


def mascarar(ra):
    """RA nunca vai inteiro para o terminal."""
    ra = str(ra)
    if len(ra) <= 2:
        return '**'
    return ra[:2] + '*' * max(1, len(ra) - 2)


class Pilar:
    def __init__(self, base, curso):
        self.base = base.rstrip('/')
        self.curso = curso
        self.cookies = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookies)
        )

    def _abrir(self, caminho, dados=None):
        url = f'{self.base}/api/{caminho}'
        corpo = None
        cabecalhos = {
            'Accept': 'application/json',
            'User-Agent': 'simulado-enade-import/1.0',
        }
        if dados is not None:
            corpo = json.dumps(dados).encode('utf-8')
            cabecalhos['Content-Type'] = 'application/json'
        pedido = urllib.request.Request(url, data=corpo, headers=cabecalhos)
        with self.opener.open(pedido, timeout=TEMPO_LIMITE) as resposta:
            tipo = resposta.headers.get('Content-Type', '')
            texto = resposta.read().decode('utf-8', 'replace')
        if 'json' not in tipo.lower():
            raise ValueError('o pilar devolveu HTML em vez de JSON (sessão não abriu?)')
        return json.loads(texto)

    def entrar(self, ra):
        try:
            self._abrir('login', {'ra': ra, 'curso': self.curso})
            return None
        except urllib.error.HTTPError as erro:
            corpo = erro.read().decode('utf-8', 'replace')
            try:
                mensagem = json.loads(corpo).get('message')
            except ValueError:
                mensagem = None
            if erro.code in (401, 404):
                return mensagem or 'RA não encontrado'
            return f'login respondeu {erro.code}'
        except Exception as erro:  # rede, timeout, JSON torto
            return str(erro)

    def aluno(self):
        dados = self._abrir('student')
        try:
            evolucao = self._abrir('evolucao')
        except Exception:
            # a evolução é opcional: sem ela, ainda dá para mostrar as áreas
            evolucao = {}
        return dados, evolucao


def ler_ras(caminho):
    """Aceita CSV com cabeçalho `ra` ou uma coluna por linha."""
    with open(caminho, encoding='utf-8-sig', newline='') as arquivo:
        primeira = arquivo.readline()
        arquivo.seek(0)
        if ',' in primeira:
            leitor = csv.DictReader(arquivo)
            campo = next(
                (c for c in (leitor.fieldnames or []) if normalizar(c) == 'ra'),
                None,
            )
            if campo is None:
                raise SystemExit('O CSV precisa de uma coluna `ra`.')
            valores = [linha.get(campo, '') for linha in leitor]
        else:
            valores = [linha for linha in arquivo]

    vistos = set()
    ras = []
    for valor in valores:
        ra = str(valor or '').strip()
        if not ra or normalizar(ra) == 'ra':
            continue
        if ra not in vistos:
            vistos.add(ra)
            ras.append(ra)
    return ras


def resumir(dados, evolucao):
    """Do JSON do pilar para o formato da tabela `desempenho_papel`."""
    aluno = dados.get('aluno') or {}
    turma = dados.get('turma') or {}
    simulado = dados.get('simulado') or {}
    areas_turma = dados.get('areas_turma') or {}

    if aluno.get('participou_mcq') is False:
        raise ValueError('só fez a discursiva (sem múltipla escolha)')

    areas = {}
    for nome, valor in (aluno.get('areas') or {}).items():
        if not isinstance(valor, dict):
            continue
        total = inteiro(valor.get('total'), 0)
        if total <= 0:
            continue
        da_turma = areas_turma.get(nome) or {}
        areas[nome] = {
            'total': total,
            'percentual': percentual(valor.get('percentual')),
            'turma': percentual(da_turma.get('percentual')) if isinstance(da_turma, dict) else None,
        }

    total = inteiro(turma.get('total_questoes'), 0)
    if total <= 0:
        total = sum(a['total'] for a in areas.values())
    if total <= 0:
        raise ValueError('o pilar não informou o total de questões')

    acertos = inteiro(aluno.get('acertos'), 0)
    pct = percentual(aluno.get('percentual'))
    if pct is None:
        pct = acertos / total
    pct = max(0.0, min(1.0, pct))

    prioridades = []
    for item in (evolucao.get('areas_prioritarias') or []):
        if not isinstance(item, dict) or not item.get('area'):
            continue
        prioridades.append({
            'area': item['area'],
            'percentual': percentual(item.get('percentual_ultimo')),
            'tendencia': item.get('tendencia'),
        })

    discursiva = aluno.get('dissertativa')
    if isinstance(discursiva, dict):
        discursiva = {
            'nota_1': numero(discursiva.get('nota_1'), None),
            'nota_2': numero(discursiva.get('nota_2'), None),
        }
        if discursiva['nota_1'] is None and discursiva['nota_2'] is None:
            discursiva = None
    else:
        discursiva = None

    return {
        'simulado_id': str(simulado.get('id') or 'papel'),
        'rotulo': str(simulado.get('label') or simulado.get('titulo') or 'Simulado em papel')[:120],
        'acertos': acertos,
        'total': total,
        'percentual': pct,
        'areas': areas,
        'prioridades': prioridades,
        'turma': {
            'total_questoes': total,
            'media_acertos': numero(turma.get('media_acertos'), None),
            'mediana_acertos': numero(turma.get('mediana_acertos'), None),
        },
        'discursiva': discursiva,
    }


def sql_do_retrato(ra, retrato, curso):
    """Um insert que acha a conta pelo RA e não duplica no reimport."""
    valores = ', '.join([
        sql_texto(curso),
        sql_texto(retrato['simulado_id']),
        sql_texto(retrato['rotulo']),
        str(retrato['acertos']),
        str(retrato['total']),
        sql_num(retrato['percentual']),
        sql_json(retrato['areas']),
        sql_json(retrato['prioridades']),
        sql_json(retrato['turma']),
        sql_json(retrato['discursiva']) if retrato['discursiva'] else 'null',
    ])
    return f"""
-- RA {mascarar(ra)}
insert into public.desempenho_papel
	(usuario_id, curso, simulado_id, rotulo, acertos, total, percentual,
	 areas, prioridades, turma, discursiva)
select m.usuario_id, {valores}
from public.membros m
where m.ra = {sql_texto(ra)}
order by m.entrou_em
limit 1
on conflict (usuario_id, curso, simulado_id) do update set
	rotulo = excluded.rotulo,
	acertos = excluded.acertos,
	total = excluded.total,
	percentual = excluded.percentual,
	areas = excluded.areas,
	prioridades = excluded.prioridades,
	turma = excluded.turma,
	discursiva = excluded.discursiva,
	importado_em = now();
"""


def conferir_materias(areas):
    """Quais nomes de área do pilar não casam com a taxonomia do site."""
    try:
        taxonomia = json.loads(MATERIAS.read_text(encoding='utf-8'))
    except Exception:
        return []
    chaves = set()
    for materia in list(taxonomia.get('ce', [])) + list(taxonomia.get('fg', [])):
        for chave in (materia.get('id'), materia.get('nome'), materia.get('oficial')):
            if chave:
                chaves.add(normalizar(chave))
        for chave in materia.get('ava') or []:
            chaves.add(normalizar(chave))

    def casa(nome):
        n = normalizar(nome)
        if not n:
            return True
        if n in chaves:
            return True
        # mesma regra do `materiaPorArea` no app: prefixo, o mais específico
        for chave in chaves:
            if len(chave) >= 8 and (chave.startswith(n + ' ') or n.startswith(chave + ' ')):
                return True
        return False

    return [nome for nome in areas if not casa(nome)]


def main():
    parser = argparse.ArgumentParser(description='Importa o simulado em papel do pilar.')
    parser.add_argument('--ras', required=True, help='CSV com a coluna ra (ou um RA por linha)')
    parser.add_argument('--sql', default=str(SQL_PADRAO), help='arquivo SQL de saída')
    parser.add_argument('--base', default=BASE_PADRAO, help='URL do pilar (para teste local)')
    parser.add_argument('--curso', default=CURSO_PADRAO, help='id do curso no pilar')
    args = parser.parse_args()

    ras = ler_ras(args.ras)
    if not ras:
        print('Nenhum RA no CSV.')
        return 1

    pilar = Pilar(args.base, args.curso)
    pedacos = []
    falhas = []
    nomes_areas = set()
    ok = 0

    for ra in ras:
        erro = pilar.entrar(ra)
        if erro:
            falhas.append((ra, erro))
            print(f'  {mascarar(ra)}: {erro}')
            time.sleep(PAUSA)
            continue
        try:
            dados, evolucao = pilar.aluno()
            retrato = resumir(dados, evolucao)
        except Exception as erro:
            falhas.append((ra, str(erro)))
            print(f'  {mascarar(ra)}: {erro}')
            time.sleep(PAUSA)
            continue

        nomes_areas.update(retrato['areas'])
        pedacos.append(sql_do_retrato(ra, retrato, 'engcomp'))
        ok += 1
        print(f'  {mascarar(ra)}: ok ({retrato["acertos"]}/{retrato["total"]})')
        time.sleep(PAUSA)

    cabecalho = f"""-- Simulado em papel importado do pilar em {datetime.now(timezone.utc).astimezone().strftime('%d/%m/%Y %H:%M')}.
-- Gerado por supabase/importar-pilar.py. Rodar no SQL Editor do Supabase.
-- {ok} retrato(s) importado(s); {len(falhas)} RA(s) sem retrato.
--
-- O insert acha a conta por `membros.ra`; RA sem conta no site não grava nada.
-- O select no fim lista os RAs sem conta e os RAs repetidos.
"""
    for ra, erro in falhas:
        cabecalho += f'-- falhou no pilar: {mascarar(ra)} ({erro})\n'
    cabecalho += '\nbegin;\n'
    rodape = '\ncommit;\n\n-- Diagnóstico: RA sem conta no site (não importado) ou RA usado por\n-- mais de uma conta (o import gravou na matrícula mais antiga).\n'
    valores = 'values ' + ', '.join('(' + sql_texto(ra) + ')' for ra in ras)
    rodape += f"""select 'sem conta' as problema, v.ra, null::bigint as contas
from ({valores}) v(ra)
where not exists (
	select 1 from public.membros m where m.ra = v.ra
)
union all
select 'RA repetido' as problema, v.ra, count(distinct m.usuario_id) as contas
from ({valores}) v(ra)
join public.membros m on m.ra = v.ra
group by v.ra
having count(distinct m.usuario_id) > 1
order by 1, 2;
"""

    saida = Path(args.sql)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(cabecalho + ''.join(pedacos) + rodape, encoding='utf-8')
    # o SQL tem os RAs completos no `where`; é dado pessoal, não fica legível
    saida.chmod(0o600)

    sem_par = conferir_materias(nomes_areas)
    print(f'\n{ok} de {len(ras)} importados.')
    print(f'SQL: {saida}')
    if sem_par:
        print('Áreas do pilar sem par em materias.json (o site mostra o nome cru):')
        for nome in sorted(sem_par):
            print(f'  - {nome}')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
