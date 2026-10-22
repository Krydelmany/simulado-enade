# Decisões de produto e arquitetura

Registro curto do **que** decidimos e **por quê**. Decisão nova entra no fim
com número novo; decisão revista não é apagada: marque **Revista em DD/MM**
e aponte para a que a substitui. O contexto completo (público, requisitos,
cronograma) está em `docs/PRODUTO.md`.

Decididas em 21/10/2026 (Giovani + Claude), a partir da conversa com o
professor: ele viu o site, disse que pode virar produto, perguntou se havia
autenticação para coletar dados dos alunos, sugeriu painel do professor e
ranking, e se ofereceu para rodar o app com a turma antes do ENADE
(**29/11/2026**).

---

### D1. Público e escopo do piloto

**Decisão:** o piloto é a turma de Eng. de Computação da Unisalesiano que
faz o ENADE em 29/11/2026, com o professor acompanhando. O escopo é só ENADE
de Eng. de Computação.

**Por quê:** o produto é B2B2C. O aluno usa, o professor acompanha e, no
futuro, quem paga é a faculdade, porque o Conceito ENADE pesa na nota do
curso no MEC. Uma turma real com prazo real valida as duas pontas. Abrir para
o público geral antes disso é gastar esforço em cadastro e suporte sem
saber se o produto funciona.

**Revisar:** em dezembro, com os números do piloto (ver métricas em `PRODUTO.md`).

### D2. Conta opcional

**Decisão:** o site continua funcionando sem conta, com o progresso no
aparelho. A conta só serve para entrar numa turma (painel, ranking) e
sincronizar.

**Por quê:** o que faz o aluno usar hoje é abrir e estudar. Login
obrigatório derruba a adesão, que é o risco número 1 do piloto. E só
coletamos dado de quem escolheu entrar.

### D3. Stack do piloto: site estático + Supabase

**Decisão:** continua SvelteKit com `adapter-static` na Vercel. O navegador
fala direto com o **Supabase** (Postgres + Auth + RLS) pelo
`@supabase/supabase-js`, carregado só quando precisa. Login com **Google**,
com link por e-mail como alternativa. A permissão mora no banco (RLS e
funções que conferem o papel), não em endpoint. A Hostinger fica no máximo
para o domínio.

**Por quê:** com 39 dias até a prova, é o caminho com menos peças. Não tem
servidor nosso para manter, o deploy continua o mesmo, e o plano gratuito
aguenta uma turma com folga. O Postgres é portável: se um dia precisarmos
de servidor próprio, os dados e o schema vão junto.

**Alternativas descartadas:**
- SvelteKit com servidor: correção no servidor (D9) e mais controle, mas não cabe no prazo.
- Vercel + Neon + auth própria: mais peças.
- Homelab: cai junto com a internet de casa.
- Hostinger compartilhada: PHP, sem Postgres.

**Revisar:** antes de abrir para outras turmas (ver D9 e D11).

### D4. Uma linha por resposta, com fila offline

**Decisão:** a tabela central é `respostas` (quem, questão, matéria, modo,
resultado, tempo, quando). Painel e ranking são consultas sobre ela. No
aparelho, cada resposta entra numa fila (`enade-nuvem-fila`) e sobe em lotes.
O id é gerado no aparelho, então reenviar não duplica. O histórico antigo do
`localStorage` **não** migra, porque é agregado e não tem a data de cada
resposta.

**Por quê:** guardar o fato, e não o resumo, deixa criar qualquer visão
depois (por semana, por matéria, por simulado) sem mudar o que o app grava.
A fila faz o site continuar funcionando com internet ruim.

### D5. Professor vê a turma só pelas funções do painel

**Decisão:** a tabela `respostas` só deixa o próprio aluno ler. O professor
lê a turma pelas funções `painel_*`, que conferem se ele é professor
**daquela** turma. Quem cadastra professor e turma é o admin (nós), por SQL.
Não existe "virar professor" pelo site.

**Por quê:** um esquecimento numa policy vazaria dado de aluno. Concentrar o
acesso do professor em 4 funções testadas (`supabase/testes/rls.test.mjs`)
deixa isso auditável.

### D6. Identificação: nome do Google, RA opcional, apelido no ranking

**Decisão:**
- O nome vem do Google.
- O **RA é opcional** e fica na matrícula da turma (não no perfil).
- O professor vê nome, RA (se houver) e desempenho.
- O ranking mostra só o **apelido**, que é único na turma.
- O aluno pode sair do ranking.

**Por quê:** o professor precisa reconhecer o aluno. O nome do Google
normalmente basta, e o RA ajuda a cruzar com a lista de chamada. RA
obrigatório é mais um campo para errar e mais dado pessoal guardado sem
necessidade (minimização da LGPD). Ele fica na matrícula porque é da
faculdade: outra turma ou instituição não precisa dele.

### D7. LGPD no piloto

**Decisão:**
- Consentimento explícito ao entrar na turma (o texto diz o que o professor vê).
- O aluno pode sair da turma ou **apagar a conta** sozinho. Perfil, matrículas e respostas vão juntos.
- Falta uma página curta de privacidade antes do lançamento (pendência em `PRODUTO.md`).

### D8. Ids de questão não mudam; o curso vai na resposta

**Decisão:** os ids (`2019-CE-Q09`, `GER-…`) continuam como estão. A tabela
`respostas` tem a coluna `curso` (padrão `engcomp`), e as consultas sempre
filtram por ela.

**Por quê:** prefixar os ids obrigaria a migrar o `localStorage` de todo
mundo (erros, revisar, histórico, prova salva), sem ganho no piloto. Quando
entrar outro curso, o par `(curso, questao_id)` já é único.

### D9. No piloto, o gabarito continua no navegador

**Decisão:** a correção continua no navegador, como hoje. **Risco aceito:**
quem abrir o DevTools consegue ver as respostas e inflar o ranking.

**Por quê:** levar a correção para o servidor muda o fluxo do treino inteiro
(cada resposta vira uma ida ao servidor, e o modo offline acaba). Não cabe
em 39 dias. Numa turma de conhecidos, com o professor olhando, o custo de
trapacear é social. O ranking é estímulo, não nota.

**Revisar:** é obrigatório antes de abrir para turmas desconhecidas ou de
cobrar. Aí a correção vai para o servidor (SvelteKit com servidor ou Edge
Function).

### D10. O material do professor fica para depois

**Decisão:** não entra agora. O banco continua em JSON no repositório
**público**. Quando precisarmos de conteúdo além das provas do INEP e das
geradas, o material dele vai para tabelas no Supabase, com acesso só para
quem está logado. Material de terceiro nunca vai para o repositório público.

### D11. Custos e limites dos planos grátis

**Decisão:** o piloto roda no grátis (Vercel Hobby + Supabase Free).

**Atenção:**
- O **Vercel Hobby não permite uso comercial**. Ao cobrar, é Vercel Pro ou Cloudflare Pages.
- O **Supabase Free pausa o projeto depois de cerca de 1 semana sem acesso**. Durante o piloto o uso é diário; depois da prova, alguém precisa abrir o site ou o projeto pausa.
- O **e-mail embutido do Supabase** manda poucos e-mails por hora. Por isso o Google é o login principal. Para escalar o link por e-mail, configurar um SMTP próprio (ex.: Resend).

Conferir os limites atuais nas páginas de preço antes de cada mudança de fase.
