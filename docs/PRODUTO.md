# Produto: Simulado ENADE (piloto com a turma)

Atualizado em 21/10/2026. Decisões numeradas (D1…) em `docs/DECISOES.md`.

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

### Próximos, em ordem de prioridade

1. **P1: Simulado agendado.** O professor escolhe a data e a turma inteira
   faz **a mesma prova** (mesmo sorteio), e o painel mostra o resultado
   consolidado por matéria. É a função de maior valor para o professor e o
   que mais puxa adesão. Precisa de uma tabela `simulados` (turma, data, ids
   sorteados) e de o simulado aceitar uma prova "dada" em vez de sortear.
2. **P2: Página de privacidade** (curta: o que coletamos, quem vê, como
   apagar). É obrigatória antes do lançamento de 01/11.
3. **P3: Reportar erro na questão.** Um botão que grava numa tabela. As
   resoluções feitas por IA ainda não foram auditadas, e com o professor
   olhando, erro custa credibilidade.
4. **P4: Exportar o painel em CSV**, para o professor levar à coordenação.
5. **P5: Analytics de produto** (PostHog): funil e retenção.
6. **Depois do piloto:**
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

   -- e-mail do professor → vira professor da turma
   insert into public.membros (turma_id, usuario_id, papel, apelido)
   select '<id da turma>', id, 'professor', 'Prof'
   from auth.users where email = '<email do professor>';
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
