# Produto: Simulado ENADE (piloto com a turma)

Atualizado em 22/10/2026. Decisões numeradas (D1…) em `docs/DECISOES.md`.

## Problema

O aluno chega ao ENADE sem preparo e sem motivo para se esforçar, porque a
nota não conta para ele. Quem sente o problema é o **curso**: o Conceito
ENADE entra na nota do curso no MEC. Hoje o professor não tem como saber se
a turma está estudando, nem onde ela está fraca, antes da prova.

## Quem é quem

| Papel | Quem | O que quer |
|---|---|---|
| Usuário | Aluno concluinte | Estudar rápido, no celular, sem burocracia |
| Defensor | Professor (quase 2º coordenador) | Ver adesão e pontos fracos da turma; puxar a turma para estudar |
| Pagador (futuro) | Coordenação / faculdade | Conceito ENADE melhor |

O professor se ofereceu para rodar o app com a turma e tem material próprio.
O material fica para quando faltar conteúdo (D10).

## Prazo

**ENADE: domingo, 29/11/2026.** Em 21/10 faltam 39 dias. Tudo se organiza
para a turma ter **pelo menos 3 semanas de uso** antes da prova.

| Quando | O quê | Quem |
|---|---|---|
| até sex 24/10 | Criar o Supabase + login Google + variáveis na Vercel; publicar o preview da branch `backend-turma`; mostrar ao professor | Giovani + Leo |
| 25/10 – 31/10 | Piloto fechado: professor + 3 a 5 alunos usam de verdade; corrigir o que aparecer; página de privacidade | Giovani + Leo |
| **sáb 01/11** | **Lançamento para a turma**: o professor manda o link do convite | Professor |
| até 08/11 | Simulado agendado pelo professor (P1 abaixo) | Giovani + Leo |
| 15/11 e 22/11 | Simulados da turma inteira (sugestão ao professor) | Professor |
| 29/11 | ENADE | — |
| dezembro | Números do piloto + conversa com o professor e a coordenação | Todos |

## Requisitos

### MVP (feito na branch `backend-turma`, falta só ligar)

- [x] Login com Google ou link por e-mail. A conta é opcional (D2).
- [x] Entrar na turma pelo **link/código do convite**, com apelido, RA opcional e consentimento (D6, D7).
- [x] Cada resposta (treino, estudo, simulado) sobe para o servidor, com fila offline (D4).
- [x] **Ranking da turma** (semana / geral) por acertos, só com apelido, com opção de sair.
- [x] **Painel do professor** (`/professor/?turma=…`):
  - números da turma: alunos, ativos em 7 dias, respondidas, acerto;
  - **Alunos**: nome, RA, últimos 7 dias, total, acerto, última vez;
  - **Matérias**: acerto por matéria, da pior para a melhor (oficiais e geradas separadas);
  - **Questões**: as que a turma mais erra (mínimo de 3 tentativas);
  - **Semanas**: evolução semana a semana.
- [x] Sair da turma; apagar a conta (LGPD).
- [x] Contagem de dias até a prova na tela da turma e no painel.

### Feito em 22/10 (branch `piloto-turma`, precisa da migração 2)

- [x] **P1: Simulado agendado.** Na aba **Simulados** do painel, o professor
  dá nome, abertura e fechamento e clica em "Sortear a prova e agendar". A
  turma inteira recebe **a mesma prova** (D12):
  - o aluno vê o simulado em `/simulado/` e em `/conta/`;
  - antes de abrir, a lista de questões não chega ao aluno;
  - o resultado aparece por aluno (quem não fez também), por matéria e com
    as questões que a turma mais errou.
- [x] **P2: Página de privacidade** em `/privacidade/`, com link no rodapé
  e no consentimento da turma.
- [x] **P3: Reportar erro na questão.** Fica no fim de cada questão, fora da
  prova, e funciona sem conta (D13). Os reportes ficam na tabela `reportes`
  do Supabase, que lemos no Table Editor.
- [x] **P4: Exportar em CSV**: o botão "Baixar planilha" na aba Alunos e no
  resultado de cada simulado. O arquivo abre direto no Excel em português.
- [x] Sair da turma pede confirmação, e o professor não tem esse botão
  (antes, um toque sem querer tirava o painel dele).

- [x] Visitas ao site (D14): contagem própria no Supabase, com o funil do
  convite. Na home, quem não entrou na conta vê "Tem turma? Entre com o
  código".

### Próximos, em ordem de prioridade

1. **P5: Analytics de produto** (PostHog): retenção e eventos dentro das
   telas. As visitas (D14) já cobrem o básico até lá.
2. **Ler os reportes** toda semana durante o piloto (SQL abaixo).
3. **Depois do piloto:**
   - correção no servidor (D9);
   - outras turmas e cursos;
   - material do professor (D10);
   - cobrança.

### Fora de escopo agora

Pagamento, app nativo, outros cursos, editor de questões, tutor com IA.

## Métricas do piloto

- **Adesão:** % da turma que entrou e % ativa por semana (meta: metade ativa toda semana).
- **Volume:** questões por aluno por semana.
- **Evolução:** acerto nos simulados de 15/11 e 22/11 comparado ao começo.
- **A que vende:** Conceito ENADE da turma comparado ao da edição anterior. O resultado sai meses depois da prova.

## Riscos

1. **Os alunos não usarem.** Mitigação: convite direto do professor, simulados coletivos e ranking.
2. **Prazo.** O que não estiver pronto em 01/11 entra depois, com a turma já usando.
3. **Conteúdo errado:** resoluções feitas por IA sem auditoria (P3).
4. **Trapaça no ranking:** o gabarito está no navegador (D9).
5. **Depender de uma pessoa só.** Se o professor sair, o piloto para. Envolver a coordenação cedo.
6. **Equipe de 2 (Giovani e Leo).** Se virar produto, combinar por escrito quem é dono do quê antes de ter receita.

## Ligar o backend (passo a passo, uma vez)

1. **Supabase:** criar o projeto na região **South America (São Paulo)**.
   Rodar `supabase/migrations/*.sql` no SQL Editor, em ordem.
2. **Google:** no Google Cloud Console, criar um OAuth Client (Web), com o
   redirect `https://<ref>.supabase.co/auth/v1/callback`. No Supabase, em
   Authentication → Providers → Google, colar o client id e o secret.
3. **URLs de volta:** no Supabase, em Authentication → URL Configuration,
   definir o **Site URL** como o domínio de produção. Em Redirect URLs,
   colocar o de produção e o dos previews da Vercel (`https://*.vercel.app/**`).
4. **Vercel:** em Settings → Environment Variables, criar
   `VITE_SUPABASE_URL` e `VITE_SUPABASE_ANON_KEY` (Settings → API do
   Supabase), em Production e Preview. Sem elas, o site continua 100% local.
5. **Turma e professor:** o professor entra uma vez pelo site (para existir o
   perfil). Depois, no SQL Editor:

   ```sql
   insert into public.turmas (curso, instituicao, nome, data_prova, codigo)
   values ('engcomp', 'Unisalesiano', 'Eng. de Computação 2026', '2026-11-29', 'ENGC26')
   returning id;

   -- e-mail do professor → vira professor da turma. O `on conflict` cobre
   -- o professor que já tinha entrado pelo convite (como aluno).
   insert into public.membros (turma_id, usuario_id, papel, apelido, consentiu_em)
   select '<id da turma>', id, 'professor', 'Prof', now()
   from auth.users where email = '<email do professor>'
   on conflict (turma_id, usuario_id) do update set papel = 'professor';
   ```

6. **Migrações novas:** cada arquivo de `supabase/migrations/` roda **uma
   vez**, em ordem, no SQL Editor, e **antes** do deploy que usa o arquivo.
   Hoje são três: `20261021000000_turmas.sql`,
   `20261022000000_simulados_reportes.sql` e `20261022010000_visitas.sql`.

### Ver as visitas ao site (D14)

No Table Editor, abra a view **`visitas_por_dia`**: visitas, pessoas
(aparelhos diferentes), quantas abriram o convite, quantas estavam logadas
e quantas no celular. Para o funil do convite e as origens:

```sql
-- abriram o convite x entraram na turma (desde o início)
select
  (select count(distinct aparelho) from public.visitas where convite) as abriram_convite,
  (select count(*) from public.membros where papel = 'aluno') as entraram_na_turma;

-- de onde as pessoas chegam
select origem, count(distinct aparelho) as pessoas
from public.visitas where origem is not null
group by 1 order by 2 desc;

-- páginas mais abertas na última semana
select caminho, count(*) as visitas, count(distinct aparelho) as pessoas
from public.visitas where criado_em > now() - interval '7 days'
group by 1 order by 2 desc;
```

### Ler os reportes de erro

```sql
select criado_em, questao_id, motivo, detalhe
from public.reportes where resolvido_em is null order by criado_em desc;

-- depois de corrigir (ou ver que não era erro):
update public.reportes set resolvido_em = now() where questao_id = '2019-CE-Q09';
```

   O convite é `https://<site>/conta/?turma=ENGC26`. Use um código de 6 a 12
   caracteres, sem 0/O/1/I/L.

## Desenvolver sem Supabase

`supabase/testes/servidor-local.mjs` imita o Supabase na sua máquina, com a
mesma migração, a mesma RLS e uma turma de exemplo com respostas:

```sh
cd supabase/testes && npm install
npm test                      # 19 testes de permissão (RLS) num Postgres de verdade
node servidor-local.mjs       # http://127.0.0.1:54321
# outro terminal, em app/:
VITE_SUPABASE_URL=http://127.0.0.1:54321 VITE_SUPABASE_ANON_KEY=local npm run dev
```

"Entrar com Google" abre uma página do dublê para escolher quem você é
(professora, Ana, Beto ou um aluno novo). O código da turma de exemplo é `ENGC26`.
