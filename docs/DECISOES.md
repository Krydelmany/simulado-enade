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

**Revista em 22/10:** o ranking passou a mostrar o nome (ver D15).

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

**Atualização (27/10/2026):** o checkbox "Concordo…" saiu do formulário da
turma. Era mais um toque obrigatório num formulário que já vem preenchido
pelo convite. O aviso do que o professor vê ficou embaixo do botão, com o
link para `/privacidade/`, e o toque em "Entrar na turma" é o aceite. O
banco continua recusando `p_consentiu = false`. "Aparecer no ranking"
continua, marcado por padrão.

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

### D12. Simulado agendado: o professor sorteia, o banco guarda a lista

Decidida em 22/10/2026.

**Decisão:**
- O professor sorteia a prova no próprio navegador, com o mesmo
  `montarProva` do simulado individual. O banco guarda só a lista de ids,
  na ordem da prova (`simulados.questoes`).
- O aluno monta a prova a partir dessa lista. Se a lista não couber no banco
  do site (questão que saiu, formato novo), a prova não começa: corrigir por
  posição com outra questão daria nota errada.
- Cada resposta sobe com `simulado_id`, e o resultado é uma consulta sobre
  `respostas`, como o resto do painel.
- Vale a **primeira** resposta de cada questão: refazer depois de ver a
  correção não muda a nota. A discursiva fica fora (é autoavaliada).
- Antes de abrir, a lista não chega ao aluno.
- Resposta com `simulado_id` de outra turma entra **sem** o vínculo, em vez
  de ser recusada.

**Por quê:**
- Sortear no servidor exigiria levar o banco de questões para o Supabase,
  que é o trabalho da correção no servidor (D9) e não cabe no prazo.
- Recusar a resposta travaria a fila do aparelho: o lote inteiro voltaria
  com erro para sempre, levando junto as respostas do treino.

### D13. Reportar erro não exige conta

Decidida em 22/10/2026.

**Decisão:** o botão "Achou um erro nesta questão?" funciona para quem
estuda sem conta. O reporte vai para a tabela `reportes`, que ninguém lê
pelo site; nós lemos no painel do Supabase. O teto é de 20 por hora por
pessoa logada e de 200 por hora somando os anônimos.

**Por quê:** as resoluções foram escritas por IA e ainda não foram
auditadas, e quem acha erro de gabarito não é só quem tem conta. Exigir
login perderia justamente o aviso que mais importa.

### D14. Visitas contadas no próprio banco, sem identificar a pessoa

Decidida em 22/10/2026.

**Decisão:** cada página aberta vira uma linha em `visitas`, gravada pela
função `registrar_visita`. A linha guarda:
- a página, sem a query;
- se veio pelo convite;
- o domínio de onde a pessoa chegou;
- se é celular ou computador;
- se estava logada;
- um uuid sorteado no navegador (`enade-aparelho`).

Não guarda nome, e-mail, IP nem o id da conta. Com "não rastrear" ligado,
nada é enviado. O envio é um `fetch` direto, sem o `supabase-js`.

**Por quê:** o painel só via quem já tinha entrado na turma. A pergunta do
lançamento é outra: quantos abriram o convite e desistiram antes de entrar.
Um serviço de analytics de fora é mais uma conta, mais um aviso de
privacidade e, no plano grátis, mais um limite. O uuid conta pessoas em vez
de cliques sem ligar a visita a ninguém.

**Revisar:** quando entrar o P5 (PostHog ou parecido).

### D15. O ranking mostra o nome, sem apelido à parte

Decidida em 22/10/2026 (substitui o "apelido no ranking" do D6).

**Decisão:**
- O formulário da turma pede só o **nome**, que vem preenchido com o do
  Google.
- O ranking mostra `perfis.nome`; trocar o nome em "Sua conta" muda o
  ranking na hora.
- `membros.apelido` continua no banco, preenchido com o começo do nome,
  só como reserva. O índice que exigia apelido único saiu.
- Quem não quer ser visto pelos colegas desmarca "Aparecer no ranking".
  O consentimento e a `/privacidade/` dizem que a turma vê o nome.

**Por quê:** pedir nome e apelido no mesmo formulário ficou repetido, e a
turma se conhece pelo nome. Com o apelido único, dois "João" seriam
barrados na entrada.

### D16. Métricas do painel: só o que muda uma decisão do professor

Decidida em 22/10/2026, com base em como ferramentas de avaliação fazem: o
relatório de estatística de questionário do Moodle (acerto e análise de
respostas por questão), os relatórios do ASSISTments (primeira tentativa,
dificuldade da questão e o erro mais comum) e os relatórios de curso do
INEP (acerto por questão e por conteúdo).

**Decisão:**
- **Acerto = primeira tentativa** de cada aluno a cada questão objetiva.
  Refazer a revisão até acertar não infla o aluno, a matéria nem a turma.
  O volume (quantas respondeu) continua contando tudo.
- **A discursiva fica fora** de todo acerto: é autoavaliada.
- **Percentual só com amostra mínima**, com o `n` sempre ao lado.
- **Evolução = simulado contra simulado** (mesma prova para a turma toda).
  O acerto semana a semana saiu: ele sobe e desce com a dificuldade das
  questões que cada um pegou, não com o aprendizado.
- **Por questão, o erro mais comum** (a letra errada mais marcada). É o que
  vira aula: "40% marcaram C" diz qual é o engano. Para isso, cada resposta
  passa a guardar a alternativa (`respostas.escolha`).
- **Ranking por questões diferentes**: repetir a mesma questão não sobe.
- Cada bloco responde a uma pergunta do professor: a turma está
  estudando? quem sumiu? onde ela erra? o que ninguém viu? está melhorando?
  Número que não responde nenhuma ficou de fora ("onde o aluno estuda",
  acerto semanal).

**Por quê:** número que só parece informação leva a decisão errada. Antes
o painel contava toda tentativa, misturava a discursiva autoavaliada no
acerto e mostrava acerto semanal, que não mede evolução.

### D17. Simulado em papel: retrato importado, somente leitura

Decidida em 27/10/2026, quando o professor já tinha o resultado do simulado
em papel no site dele (pilar.ia.br/enade2026) e a turma começou a usar o
nosso site.

**Decisão:**
- O resultado do simulado em papel é **importado uma vez** do site do
  professor para o nosso Supabase. O dado lá é fixo: a prova já aconteceu e
  não há outro simulado marcado.
- A tabela `desempenho_papel` guarda só o resumo por aluno e por simulado:
  acertos, total, percentual, percentual por área, prioridades com tendência,
  média/mediana da turma e as notas das discursivas quando existirem.
  **Não** guarda cookie, resposta por questão nem uma segunda cópia do RA.
- O aluno vê o próprio retrato em `/desempenho/` e pode informar/trocar o RA
  em `/conta/` (o RA é opcional e fica na matrícula). O professor vê o do
  aluno na ficha do painel, pela RPC `painel_papel`.
- As áreas viram matérias do site por `materiaPorArea`; o botão "Treinar"
  abre `/treino/?materia=<id>`. Área sem par aparece com o nome cru e sem
  filtro.
- O `total` do retrato é o denominador do percentual: as questões que
  entraram nas áreas (43). O total da prova (44) fica em
  `turma.total_questoes`; a tela mostra os dois e avisa que 1 questão ficou
  fora das áreas.
- O cliente **não escreve** na tabela: só `select` do próprio aluno. A
  importação é um SQL gerado por `supabase/importar-pilar.py` e rodado pelo
  admin no SQL Editor. Isso também impede o aluno de inflar os próprios
  números pelo DevTools.

**Por quê:** sem CORS no pilar e com sessão por cookie, o navegador do nosso
site não consegue ler a API. Um proxy em tempo real (Edge Function) seria
mais uma peça e um deploy para um dado que não muda. Importar uma vez deixa a
página instantânea, funciona com o pilar fora do ar e põe o número no mesmo
lugar em que o professor já olha o uso do site.

**LGPD:** o RA continua opcional. Quando informado, a `/privacidade/` diz que
o resumo do simulado em papel é guardado para o aluno e o professor verem; a
tabela tem `on delete cascade` a partir de `perfis`/`auth.users`, então apagar
a conta apaga o retrato junto. Guardamos o resumo, não a prova.

**Revisar:** se houver outro simulado em papel, rode o script de novo (o
insert é idempotente por `(usuario_id, curso, simulado_id)`). Se o professor
quiser sincronizar todos os alunos de uma vez, é outra decisão: exige chave
de serviço e varredura de RAs de quem não abriu o site.

### D18. Questionário do professor: conteúdo separado, gabarito preliminar

Decidida em 28/10/2026, quando o professor passou 10 questões de POO para a
turma resolver.

**Decisão:**
- O questionário fica em `app/static/banco/poo-2026-10-28.json`, **fora**
  de `ARQUIVOS_BANCO` e do pipeline do banco. É um teste diário, não uma
  questão oficial do ENADE: não entra no treino/estudo/simulado, no
  `stats`, no ranking nem no painel do professor.
- A tela `/poo/` tem intro com "Novo"/"Lançado hoje", correção na hora e
  resultado local; a home ganha o cartão destacado antes dos modos.
- O gabarito é **preliminar**: a Q5 foi conferida no ENADE 2011 (q39); as
  outras foram resolvidas. A tela diz isso e o professor confirma em aula.
  O JSON é a fonte para corrigir.
- O código C++/Java vai no enunciado; a UML é uma imagem recortada do PDF.

**Por quê:** misturar o quiz do professor no banco oficial faria as questões
aparecerem no treino/estudo/simulado e nas métricas, e um gabarito sem
auditoria entraria como oficial. Separado, o aluno resolve o que o professor
passou hoje e o banco continua sendo só ENADE.

**Revisar:** quando o professor confirmar/corrigir o gabarito, atualize o
JSON e a data. Se o quiz virar uma trilha recorrente, aí sim vale um modelo
de curso/modo e tracking.
