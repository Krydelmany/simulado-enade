# AGENTS.md — Simulado ENADE (Engenharia de Computação)

Guia para agentes de código (Claude Code, Codex, Cursor…) e para quem chega
agora. O `README.md` é o manual para humanos. Este arquivo explica **como o
sistema funciona e quais regras não podem ser quebradas**.

Quando um doc e o código discordarem sobre **comportamento**, vale o código
(veja "Docs desatualizados", no fim). Quando o assunto for **conteúdo de
questão** (texto, gabarito, anulação), vale a folha oficial do INEP em
`fontes/`. Nem o banco nem os docs servem de referência nesse caso.

Tudo no projeto é escrito em **português do Brasil**: identificadores,
comentários, commits, PRs e textos da tela. Siga o mesmo idioma.

## O que é

É um site estático de estudo para o ENADE de Engenharia de Computação, feito
para uma turma. Não tem backend nem login. O banco de questões é um conjunto
de arquivos JSON publicados junto com o site, e o progresso do aluno fica no
`localStorage` do aparelho. O site tem três modos:

- **Treino livre** (`/treino/`): uma fila contínua e embaralhada com o banco
  **inteiro** (questões oficiais e geradas), com filtro por matéria. Há
  também um modo revisão (`/treino/?modo=revisao`), que mostra as questões
  erradas e as marcadas para revisar.
- **Estudo** (`/estudo/`): sessões de até 10 questões, com filtro opcional de
  matéria. Os níveis Fácil, Médio e Difícil usam as questões **geradas** para
  revisão, e a categoria **ENADE oficial** usa as 160 questões do INEP. Com
  uma matéria filtrada, cada nível de geradas tem só 3 questões.
- **Simulado** (`/simulado/`): reproduz a prova de 2026 (Portaria INEP nº
  161/2026), com 15 objetivas de Formação Geral (FG), 30 do Componente
  Específico (CE) e 1 discursiva, em 4 h. Tem cartão-resposta, pausa e
  correção só na entrega. A home e o simulado contam apenas as oficiais.

A branch `main` é o que está no ar: cada merge publica em produção na Vercel,
e cada PR ganha uma URL de preview.

## Mapa do repositório

```
app/                       o site: SvelteKit 2 + Svelte 5 + Tailwind 4 + Vite 6
  src/app.html             shell + script anti-flash do tema escuro
  src/app.css              design tokens (@theme inline), classes próprias, motion
  src/routes/              +layout.svelte (nav, tab bar, rodapé), +layout.js
                           (prerender), +error.svelte (404), / , treino/, estudo/,
                           simulado/
  src/lib/                 banco.js, stats.js, simulado.js, materias.js(.json),
                           resumo.js, tema.js, motion.js, foco.svelte.js,
                           sessao.js, gestos.js, camadas.svelte.js e os
                           componentes (Questao, TextoRico, SessaoTopo, BarraAcao,
                           Contador, VigiaDevTools, BordaVoltar, DicaGestos)
  static/banco/            O BANCO que o site carrega: enadeAAAA-{fg,ce}.json,
                           geradas.json e img/   ← SAÍDA de scripts
  vercel.json              build e cache headers (tem de ficar em app/)
banco/                     scripts Python que produzem e conferem o banco, mais as
                           FONTES editáveis: classificacao.json, digitadas.json,
                           geradas/NN-<materia>.json
fontes/                    PDFs oficiais do INEP (prova, gabarito, padrão de resposta)
                           + simulado-prof-2026.pdf (relatório da turma, não é banco)
revisao/                   markdown de revisão: lotes da extração (histórico) e
                           revisao/geradas/*.md (reescritos pelo geradas.py)
testes-mob/                harness Playwright de QA mobile (desatualizado)
design/                    prints antigos, anteriores à direção visual atual
README.md · PLANO.md · ROADMAP.md · INVENTARIO.md   docs de produto e de fontes
```

## Como o site funciona

### Build, rotas e navegação

- O adapter é o `adapter-static`, com `fallback: '404.html'`. O `+layout.js`
  define `prerender = true` e `trailingSlash = 'always'`. Por isso **toda
  página é renderizada em Node no build** (SSR ligado) e vira
  `build/<rota>/index.html`.
- Não há `+page.js` nem `load`: cada página chama `carregarBanco()` no próprio
  `onMount`.
- Tela nova = `routes/<nome>/+page.svelte`. Para ela aparecer, inclua-a em
  três listas escritas à mão: o array `tabs` do `+layout.svelte` (alimenta a
  nav do topo e a tab bar do celular), os links do rodapé (no mesmo arquivo)
  e, se for um modo, o array `modos` da home.
- **Não use rota com parâmetro** (`[id]`): com tudo pré-renderizado, o build
  falha. Passe o parâmetro pela query, como em `?modo=revisao`.
- Na Vercel, o Root Directory `app` é configurado **no painel**, não no
  `vercel.json`. Essa chave não existe no arquivo, e a Vercel o rejeita se
  ela aparecer.

### Carregamento do banco (`src/lib/banco.js`)

- `ARQUIVOS_BANCO` lista os 9 JSON (8 oficiais + `geradas.json`).
  `carregarBanco()` busca todos em paralelo e junta tudo num array plano.
- Cada URL leva `?v=VERSAO_BANCO`. `VERSAO_BANCO` é um hash do conteúdo de
  `static/banco/*.json`, gravado por `banco/versao.py --escrever`. O `?v=`
  existe porque o `vercel.json` serve `/banco/*` com `stale-while-revalidate`.
  Sem ele, logo depois de um deploy o navegador entregava o JSON antigo.
- O resultado fica em cache em `sessionStorage['enade-banco']` =
  `{versao, em, questoes}`. O TTL é de 6 h, e a cache é descartada quando
  `versao !== VERSAO_BANCO`. Ela só é gravada se os 9 arquivos chegaram.
- As imagens (`/banco/img/*`) não entram no hash e não levam `?v=`. Para
  corrigir uma imagem, use um nome de arquivo novo, ou aceite que o aluno a
  veja velha por uma visita.
- Questão gerada tem `fonte: 'gerada'`; sem `fonte`, é oficial (`ehGerada`).
  No Estudo, os níveis 1 a 3 são as geradas com `dificuldade` `'Fácil'`,
  `'Média'` ou `'Difícil'`, e o nível 4 (`NIVEL_ENADE`) são todas as oficiais.

### Estado do aluno (só no aparelho)

Todas as chaves têm o prefixo `enade-`:

| Onde | Chave | Conteúdo |
|---|---|---|
| localStorage | `enade-tema` | `'dark'` ou `'light'` (sem a chave, segue o sistema) |
| localStorage | `enade-xp`, `enade-erros`, `enade-revisar` | XP; ids errados; ids marcados para revisar |
| localStorage | `enade-historico` | agregado por **id de questão**, por dia e por sessão (`stats.js`) |
| localStorage | `enade-sessao` | treino pausado (`v: 2`) |
| localStorage | `enade-sessao-estudo` | estudo pausado (`v: 2`), gravado direto pela rota, fora do `stats.js` |
| localStorage | `enade-simulado` | prova em andamento ou entregue (`v: 1`) |
| localStorage | `enade-simulado-ultimo` | resumo da última prova entregue |
| localStorage | `enade-dica-gestos` | ids das dicas de gesto já vistas (`'questoes'`, `'simulado'`) |
| localStorage | `enade-streak` | legado, só lido por `getStreak` (deprecated) |
| sessionStorage | `enade-banco` | cache do banco |

Não existe servidor para migrar dados. **Qualquer mudança no formato gravado
precisa continuar lendo o formato antigo, ou descartá-lo sem quebrar.** Como
cada chave lida com isso hoje:

- **Estados de sessão** (`enade-sessao`, `enade-sessao-estudo`,
  `enade-simulado`): têm um `v`. Ao mudar a forma, suba o número e trate o
  formato antigo na leitura.
  - o estudo migra o `v: 1`;
  - o simulado descarta tudo que não for `v: 1`.
- **`enade-historico`:** grava `v: 1`, mas `normalizarEstado` ignora esse
  campo e regrava sempre `v: 1`. A migração, se precisar, entra em
  `normalizarEstado`.
- **`enade-simulado-ultimo`, `enade-xp`, `enade-erros`, `enade-revisar`,
  `enade-dica-gestos`:** não têm `v`. A leitura só descarta o que não tem a
  forma esperada.

`stats.js` nunca lança: storage bloqueado, cheio ou com JSON inválido volta
ao valor padrão, e o histórico é cortado para caber (os tetos estão em
`TETO_HISTORICO`). A forma dos dados só é validada para histórico, XP, erros
e revisar. `carregarSessao()` devolve o JSON cru, então quem chama precisa
validar. Campo novo no histórico tem de entrar em `normalizarEstado`, senão
some na próxima gravação.

### Simulado (`src/lib/simulado.js` + `routes/simulado/+page.svelte`)

- **Sorteio:**
  - Entram só oficiais, sem `ANULADA` e sem `padrao_placeholder`, e só
    discursivas do CE.
  - O sorteio é balanceado por matéria (uma de cada matéria por rodada), com
    `Math.random` e sem semente.
  - A ordem é FG 1–15, CE 16–45 e a discursiva por último.
- **O que é salvo:** a prova fica em `enade-simulado`, com os `ids` e as
  `marcas` **indexadas pela posição** na prova, não pelo id.
- **Relógio:**
  - Só corre com `tela === 'prova'`. O tempo é gravado a cada 15 s, a cada
    marcação ou navegação e em `visibilitychange`/`pagehide`.
  - Aba fechada ou recarregada não conta: a página volta à tela inicial e o
    relógio só retoma em "Continuar".
  - Aba em segundo plano ou celular bloqueado **contam**.
  - Quando as 4 h acabam, a prova é entregue sozinha.
- **Recarregar:** a prova é reconstruída pelos ids. **Se algum id não estiver
  mais no banco, a prova inteira, em andamento ou entregue, é apagada.**
- **Entrega:**
  - A correção só acontece aqui. As objetivas respondidas entram no mesmo
    histórico dos outros modos, na lista de erros (quem errou entra, quem
    acertou sai) e no XP (10 por acerto). Questão em branco fica fora de tudo.
  - A discursiva fica fora da nota. Ela é autoavaliada contra o padrão de
    resposta na revisão e vai para o histórico, sem XP.
- **Mudar o formato da prova:** mude `FORMATO` em `simulado.js` **e** suba o
  `v` em `montarProva` e em `lerProva`. O bloco de cada posição é calculado a
  partir de `FORMATO` na hora da leitura, então uma prova antiga seria
  corrigida com os blocos errados. Atualize também, na rota, o
  `FORMATO_TELA` e o "relógio de 4 horas" da lista "Como funciona", e o card
  do simulado na home. Os três repetem os números em texto.

### Gestos e o voltar do sistema

O "voltar da borda para o meio" já existe no celular: é o voltar do
sistema (as duas bordas no Android com gestos, a esquerda no iOS, o botão no
Android com 3 botões). Por isso o site não inventa outro gesto: faz o voltar
do sistema fechar a camada certa.

- **Camadas (`camadas.svelte.js`):** cada tela montada dentro da página
  (prova, resultado e revisão do simulado; quiz e fim do estudo), cada modal
  e o zoom da figura ganham uma entrada rasa no histórico (`pushState` do
  `$app/navigation`), com `page.state = { camadas, idade }`. A rota chama
  `ligarCamadas(abertas, fechar)` uma vez e o efeito mantém o histórico
  alinhado com o que está aberto.
  - **Invariante:** uma entrada com N camadas fica exatamente N entradas
    acima da base da mesma URL; `history.go(-k)` com k ≤ N nunca sai da rota.
  - **O histórico só fecha, nunca abre.** Avançar, ou cair numa entrada
    velha, é desfeito na hora: uma entrada "prova" antiga não pode religar o
    relógio. A `idade` (sempre crescente) separa voltar de avançar.
  - O voltar não pede confirmação, porque tudo já está salvo: o treino grava a
    cada resposta, o estudo volta ao seletor com "Continuar?" e a prova volta
    ao início, pausada.
  - Depois de recarregar com camadas abertas, pode sobrar no máximo um toque
    de voltar sem efeito (o Kit zera o `page.state` na hidratação).
- **`BordaVoltar`:** gesto de borda próprio, só como reserva para aparelho
  sem o do sistema. Ligado só no quiz. No iOS ele NÃO usa a borda esquerda,
  que é do Safari (seriam dois voltares de uma vez); no Android com gestos o
  sistema manda `touchcancel` e ele nunca dispara. Na base da rota leva à
  home com `goto('/')`, nunca `history.back()` (quem chegou por link direto
  sairia do site).
- **Deslizar (`gestos.js`):** a questão segue o dedo e troca com
  max(64 px, 20% da largura) ou com um peteleco (≥ 0,4 px/ms e ≥ 32 px). A
  direção bloqueada só cede 32 px (efeito elástico). O eixo só é decidido
  depois de 10 px, com o principal ≥ 1,5× o outro; parado 450 ms antes disso
  é seleção de texto e o gesto é abandonado. Os 24 px de cada borda ficam
  para o voltar do sistema. No simulado, puxar a `BarraAcao` 40 px para cima
  abre o cartão-resposta, e arrastar o cartão 80 px para baixo o fecha.
  - Só toque (mouse e caneta ficam de fora), com listeners passivos. O
    `touchend` tem `preventDefault` e os cliques dos 400 ms seguintes são
    engolidos em captura: sem isso, soltar o dedo sobre uma alternativa a
    marcava.
  - Elemento com `data-sem-gesto` (e campo de texto, seleção ativa, pinça
    ampliada, modal aberto) não começa gesto.
  - Com `prefers-reduced-motion`, nada segue o dedo e nada anima; o gesto
    continua trocando a questão.
- **`html.sem-recarregar`:** no quiz, `overscroll-behavior-y: contain`
  impede o pull-to-refresh do Chrome. Só o eixo y: o x desligaria o voltar
  por gesto do Chrome.

### Questão ANULADA

`"gabarito": "ANULADA"` dá ponto para todos no treino e no estudo: qualquer
letra conta como `certa`, sem XP e sem mexer na lista de erros. No simulado,
a anulada fica **fora do sorteio**.

## O banco de questões

### Fontes → scripts → JSON do site

O JSON em `app/static/banco/` é **gerado**. Para mudar uma questão, edite a
fonte e rode o script correspondente:

| O que mudar | Fonte (editar aqui) | Como aplicar |
|---|---|---|
| tema, dificuldade ou matéria de uma oficial | `banco/classificacao.json` (`{"<id>": [tema, dificuldade, materia]}`) | `python banco/classificar.py --banco` |
| texto de uma oficial (enunciado, alternativas, padrão, imagem) | `banco/digitadas.json` (uma entrada por id) | `python banco/digita.py --banco` e depois `python banco/paragrafo.py --banco` |
| gabarito ou `padrao_placeholder` de uma oficial | **não há fonte editável**: na extração, o gabarito vem de `fontes/*.txt` (fora do git), e o `padrao_placeholder` é calculado pelo `arruma.py` a partir do padrão lido do PDF | edite o `enadeAAAA-*.json` à mão, só depois de conferir na folha oficial. Os modos `--banco` preservam a edição; um `gerar.py` daquela prova a desfaz |
| questões geradas (Fácil/Médio/Difícil) | `banco/geradas/NN-<materia>.json` | `python banco/geradas.py` (reescreve `geradas.json` e `revisao/geradas/*.md`) |
| taxonomia de matérias | `app/src/lib/materias.json` | lida pelo app e pelos scripts (veja as regras abaixo) |
| reextrair uma prova inteira do PDF | `fontes/*.pdf` | `banco/gerar.py` (só Linux, veja "Extração") |

Depois de **qualquer** mudança no banco, rode nesta ordem:

```bash
python banco/validar.py             # tem de sair limpo (exit 0)
python banco/testes.py              # tem de passar
python banco/versao.py --escrever   # reescreve VERSAO_BANCO em app/src/lib/banco.js
```

Commite tudo junto: a fonte que você editou, os JSON de `app/static/banco/`
(mais o `.png` novo e os `revisao/geradas/*.md`, se for o caso) e o
`banco.js`.

### Esquema de uma questão

| Campo | Valores |
|---|---|
| `id` | oficial: `<edicao>-<FG\|CE>-<Q\|D><NN>` (ex.: `2019-CE-Q09`, `2014-FG-D01`); gerada: `GER-<inciso romano>-<F\|M\|D><n>` |
| `fonte` | `"gerada"`, ou ausente (= oficial) |
| `edicao` | `2014`, `2017`, `2019` ou `2023`; `null` nas geradas |
| `parte` | `"FG"` ou `"CE"` (as geradas são sempre `CE`) |
| `numero` | string: `"09"` nas oficiais, `"F1"` nas geradas |
| `tipo` | `"objetiva"` ou `"discursiva"` |
| `tema` | texto livre |
| `dificuldade` | `"Fácil"`, `"Média"` ou `"Difícil"`; **nunca "Médio"** (a tela mostra "Médio"). O `validar.py` só confere isso nas geradas: em `classificacao.json` ninguém confere |
| `materia` | um `id` de `materias.json` (as 20 áreas do CE da Portaria nº 161 + as de FG) |
| `enunciado` | `\n\n` separa parágrafos; `\n` simples só entre itens de lista (I., II., a), •) e linhas de tabela; blocos ```` ```lang ```` para código |
| `alternativas` | `{A..E}` nas objetivas; `{}` nas discursivas e nas de alternativas visuais |
| `gabarito` | `"A"` a `"E"`, ou `"ANULADA"` (só objetivas) |
| `padrao` | padrão de resposta (só discursivas) |
| `padrao_placeholder` | `true` quando o padrão oficial não tem texto utilizável |
| `imagem` | `{src: "/banco/img/<id>.png", alt}` (`legenda` é opcional) |
| `alternativas_visuais` | `true` quando as alternativas são desenho e vêm no recorte; exige `imagem` |
| `figura` | sempre `null` hoje (campo legado) |

Ordem dentro dos arquivos:

- `enadeAAAA-*.json`: discursivas primeiro, depois por `numero`. O
  `digita.py --banco` reordena assim.
- `geradas.json`: pela ordem das matérias em `materias.json`, depois
  F/M/D, depois `n`.

### Regras de conteúdo

- **Nunca preencher por dedução.** O que não deu para ler na página fica de
  fora, e a letra do gabarito vem **sempre** da folha oficial.
- **`banco/digitadas.json`** guarda o texto lido da página renderizada.
  - Chaves: `A`…`E`, `_enunciado`, `_padrao`, `_imagem {src, alt}`,
    `_alternativas_visuais: true` e `_nova {edicao, parte, numero, tipo,
    gabarito?, imagem?}`. A chave `"_"` é só comentário.
  - **Alternativa só é substituída se a entrada trouxer as CINCO letras.** Com
    menos, a letra digitada só preenche uma alternativa que está vazia
    (exceto para os ids em `SUBSTITUIR_TUDO`). Corrigir só a C não muda nada
    e não dá erro.
  - O `digita.py` só sobrepõe: apagar uma entrada não traz o texto antigo de
    volta.
  - Questão `_nova` (uma que a extração nem produziu): crie antes a linha do
    id em `classificacao.json`. Sem ela, a questão entra sem tema nem matéria
    e o `validar.py` reprova.
- **`paragrafo.py` só pode mudar espaço em branco** (as exceções são a tabela
  `GRUDADAS` e o "•" da fonte Symbol).
  - Depois do `digita.py --banco`, ele tem de dizer "0 de N questões
    reformatadas". Ele grava mesmo quando o número não é 0: nesse caso, olhe
    o `git diff` antes de seguir.
  - "NADA GRAVADO" quer dizer que o texto visível mudaria, ou que uma
    segunda passada mudaria o resultado. A lista abaixo da mensagem diz qual
    dos dois e em que questão.
- **Geradas:**
  - A fonte é `{"materia": "<id do CE>", "questoes": [{dificuldade, tema,
    enunciado, alternativas: {A..E}, gabarito}]}`. O id e o número saem da
    posição no arquivo (contador por nível + inciso da matéria). A parte é
    sempre `CE`.
  - Gerada é só objetiva de texto: campos a mais (imagem, padrão) são
    descartados sem aviso.
  - Questão nova entra **no FIM** do arquivo da matéria. O `n` do id é um
    contador por nível dentro do arquivo, então inserir no meio, apagar ou
    trocar a dificuldade renumera os ids.
  - O `validar.py` exige pelo menos uma gerada de cada nível em cada uma das
    20 matérias do CE, e nenhuma letra com mais de 30% dos gabaritos.
    Distribua as letras.
- **`materias.json`:**
  - Mudar o `inciso` de uma matéria do CE troca todos os `GER-*` dela.
  - O `id` também é chave persistente, porque o histórico guarda `materia`.
    Para mudá-lo, troque também em `classificacao.json` e no `"materia"` de
    `banco/geradas/NN-*.json`, e rode `classificar.py --banco` e
    `geradas.py`.
  - Matéria nova no CE reprova o `validar.py` até ter geradas nos três níveis.
  - Mudar só o `nome` é livre.
- **Blocos de código:**
  - Tudo o que vem depois do ```` ``` ```` de abertura, na mesma linha, é
    tratado como linguagem e **não aparece na tela**.
  - Um ```` ``` ```` sem par sai literal ou casa com o próximo e transforma
    texto em código.
  - O `validar.py` acusa os dois casos. Se for uma linguagem nova legítima,
    acrescente-a em `LINGUAGENS`.
  - O regex `FENCE_RENDER` do `validar.py` tem de continuar idêntico ao de
    `TextoRico.svelte`.
- **Imagem:** recorte da página renderizada a 200 dpi, conferido a olho, em
  `app/static/banco/img/<id>.png`. Vídeo é link, nunca arquivo.

### Prova nova (ex.: ENADE 2026) sem reextração

1. Crie `app/static/banco/enade2026-fg.json` e `-ce.json` com `[]` e ponha os
   dois em `ARQUIVOS_BANCO`. O nome **tem** de seguir `enadeAAAA-{fg,ce}.json`,
   porque é esse padrão que o `validar.py`, o `testes.py` e os modos
   `--banco` procuram.
2. Cada questão entra em `digitadas.json` com `_nova` (número com dois
   dígitos, gabarito da folha oficial), `_enunciado`/`_padrao`, as cinco
   letras e a imagem.
3. Cada id ganha uma linha em `classificacao.json`.
4. Rode `digita.py --banco`, `paragrafo.py --banco` e depois
   validar/testes/versão.
5. Atualize os textos fixos na tela: o `META = 160` da home, o
   "2014/2017/2019/2023" do rodapé do layout e o "provas de 2014 a 2023" do
   simulado.

### Extração dos PDFs (raro; não roda nesta máquina Windows)

`banco/gerar.py <ano> <FG|CE>` reextrai uma prova e **sobrescreve** o JSON
daquela parte. A cadeia é `montar.extrair` → `digita.acrescenta` →
`classificar.aplicar` → figuras/imagens → por questão `digita.aplica →
arruma.limpa → formato.formata → qualidade.limpa → digita.finaliza` → porta
`qualidade.problema` → JSON + `revisao/lote-*.md`. Antes de mexer nela, saiba:

- **A parte vai em maiúsculas.** `fg` em minúsculas grava `[]` no JSON antes
  de quebrar.
- `digita.finaliza` tem de ser a **última** etapa da cadeia. A cadeia está
  copiada em três lugares (duas vezes no `gerar.py` e uma no `testes.py`):
  mudou a ordem, mude nos três.
- **2014/2017 vão por OCR**, porque a fonte não tem `ToUnicode`. O
  `gerar.py` não roda o OCR: antes, rode `python3 banco/ocr.py`, que grava
  `/tmp/opencode/extr/ocr/<ano>-ocr.txt`. Sem esse arquivo, o `montar` cai
  calado no `pdftotext` e extrai lixo.
- No OCR, renderize com `mutool`, não com `pdftoppm`. O recorte de figura
  (`figura.py`) usa `pdftoppm -r 200`, e ali tudo bem. O `olho.py` usa o
  mesmo `pdftoppm`, mas a 400 dpi por padrão, e grava em `revisao/img/` só
  para leitura. O `gerar.py` só aponta `imagem.src`; o PNG é recortado à
  parte.
- Se a leitura do PDF de padrão falhar, o erro é engolido: as discursivas
  saem com `padrao_placeholder: true` e a porta não reclama. Confira no
  `git diff` que nenhum padrão sumiu.
- **Dependências:** poppler (`pdftotext -bbox-layout`, `pdfinfo`,
  `pdftoppm`; o Xpdf que vem no MSYS2 não serve), `mutool`, `tesseract` com o
  idioma `por` e Pillow.
- Os `fontes/*.txt` de gabarito também são necessários e **não estão no
  repo** (o `.gitignore` ignora `*.txt`). São o texto dos PDFs de gabarito.
- Os scripts têm caminhos fixos `/root/enade-simulado` e `/tmp/opencode`, e
  os caches de `/tmp/opencode/extr/` nunca são invalidados.
- Ano novo pelo `gerar.py` precisa entrar em `montar.PROVAS`/`GABARITO`, em
  `parser.EDICOES` (numeração FG/CE da prova), em `padrao.PADRAO` e em
  `gerar.LOTE`. Sem `padrao.PADRAO` o erro é engolido, e todas as
  discursivas saem como placeholder.

Os modos `--banco` (`digita`, `paragrafo`, `classificar`) **não** precisam de
PDF nem de ferramenta externa: a manutenção do dia a dia passa por eles. Eles
só tocam `enade*.json`, nunca `geradas.json`, e não passam pela porta de
qualidade.

## Comandos

```bash
# site (dentro de app/; Node 20+, aqui há o 22)
npm install
npm run dev        # http://localhost:5173
npm run build      # gera app/build; pega erro de compilação e de SSR/prerender,
                   # mas NÃO carrega o banco nem roda o que está em onMount
npm run preview    # http://localhost:4173 — usa o servidor do SvelteKit
                   # (.svelte-kit/output), não o app/build estático

# banco (da raiz; Python só com biblioteca padrão)
python banco/validar.py
python banco/testes.py
python banco/versao.py              # só mostra; --escrever grava

# o app/build de verdade, com a 404 da Vercel (depois do build).
# Só o conteúdo imita a Vercel: o status sai 200 e os headers do vercel.json
# não são aplicados. Use rotas com barra no fim e sem query
# (/treino/?modo=revisao cai no 404.html).
python banco/servidor-404.py 8126 app/build
```

Não há lint, formatter, `svelte-check`, testes de JS nem CI. As únicas
barreiras são o build da Vercel e os scripts `validar.py`/`testes.py`.

No Windows:

- `python` é o 3.14 de `C:\Python314`, e `python3` é o alias da WindowsApps;
  os dois funcionam.
- Para os acentos saírem certos no console, use `python -X utf8 …` (funciona
  no Git Bash e no PowerShell).
- O `core.autocrlf=true` vem do gitconfig do Git for Windows. Os modos
  `--banco` e o `geradas.py` gravam LF; o `versao.py --escrever` grava CRLF.
  O autocrlf normaliza no commit.
- O `pdftotext` do MSYS2 (`/ucrt64/bin`) é o Xpdf 4.06, sem `-bbox`.

## Regras invioláveis

O que quebra em silêncio, ou longe de onde a mudança foi feita:

1. **O `id` de uma questão é chave persistente.** Histórico, erros, revisar e
   provas salvas usam o id. Trocar um id deixa dados órfãos no aparelho do
   aluno e apaga o simulado salvo, em andamento ou entregue. Nas geradas, o
   id sai da posição no arquivo e do `inciso`: inserir no meio, apagar ou
   mudar a dificuldade troca ids sem que ninguém tenha "renomeado" nada.
2. **O formato gravado no aparelho não se migra no servidor.** Mudou a forma
   de uma chave, trate o formato antigo na leitura e suba o `v` onde ele
   existe (veja "Estado do aluno").
3. **Mudou JSON do banco, rode `python banco/versao.py --escrever`.** Sem
   isso, o aluno vê o banco velho por até 6 h. Sem a flag, o script sai com 0
   mesmo desatualizado, então não serve como checagem.
4. **Não edite `app/static/banco/*.json` à mão.** O `classificar.py --banco`
   sobrescreve tema, dificuldade e matéria; o `geradas.py` regera o
   `geradas.json`; e o `testes.py` falha se o texto divergir de
   `digitadas.json`. A exceção é `gabarito`/`padrao_placeholder`, que não têm
   outra fonte (veja a tabela).
5. **Arquivo novo no banco entra à mão em `ARQUIVOS_BANCO`** e se chama
   `enadeAAAA-{fg,ce}.json`. Fora da lista, o site não busca o arquivo. Com
   outro nome, só o `versao.py` o enxerga, e ninguém o confere.
6. **Os caminhos do `.vercelignore` começam com `/`.** Um `banco` sem a barra
   casa também com `app/static/banco`, e o site vai ao ar sem nenhuma questão.
7. **O `vercel.json` fica em `app/`**, ao lado do `package.json`.
8. **SSR no build:**
   - `window`, `document`, `localStorage` e `sessionStorage` só podem ser
     usados dentro de `onMount`, `$effect` ou handlers.
   - Nos módulos `.js` de `lib/`, use guarda `typeof window` + `try/catch` em
     todo acesso a storage.
   - Ler `url.searchParams` durante o prerender derruba o build. O treino
     guarda a query num `$derived($page.url.searchParams…)`, e isso funciona
     porque nada renderizado antes de `carregou` lê esse valor. Se copiar o
     padrão, mantenha a query fora do primeiro render.
   - Não mova a leitura da query para o `onMount`: trocar
     `?modo=revisao` não remonta a página, e a troca de modo pararia de
     funcionar.
9. **Rotas sempre com barra final** (`/treino/`), por causa do
   `trailingSlash = 'always'`. O roteador normaliza a URL, então
   `$page.url.pathname` chega sempre como `/treino/`, e comparar com
   `'/treino'` nunca casa. O destaque da nav (`===`) e o `emQuiz` do layout
   (`startsWith('/treino/')`) dependem disso. Nos `href`, use a barra também.
10. **A regra do tema está em três lugares:** `temaPreferido()` e
    `scriptAntiFlash()` em `tema.js`, e o script inline de `app.html`. A regra
    é: `enade-tema` manda; sem ela, segue `prefers-color-scheme`. Mudou um
    lugar, mude os outros.
11. **`prova.marcas` é indexado por posição.** Reordenar `prova.ids` embaralha
    as respostas do aluno.
12. **`<Questao>` lê `inicial`, `revisarInicial` e `rascunhoInicial` uma
    vez só.** Envolva o componente em `{#key}` com uma chave que mude sempre
    que a questão mostrada mudar, inclusive quando o mesmo id reaparece. O
    treino usa id + volta + posição, porque a fila dá a volta.
13. **`TextoRico` é usado dentro de `<p>` e dentro do `<button>` da
    alternativa.** Ele só pode emitir elementos de frase (`<span>`, `<code>`,
    `<a>`); `<div>` ou `<pre>` quebram a hidratação. Dentro do botão, nada
    pode ser interativo.
14. **Tela de quiz fora de `/treino/` e `/estudo/`** precisa ligar
    `foco.quiz` num `$effect` e desligar no cleanup (`foco` é estado de módulo
    e sobrevive à troca de rota). Sem isso, a tab bar cobre a `BarraAcao` no
    celular e, em qualquer largura, o `<main>` fica sem o `pb-32` que impede a
    barra de esconder a última alternativa.
15. **Toda camada nova** (modal, overlay, tela montada dentro da página)
    entra no `abertas()` do `ligarCamadas` da rota, com o `fechar`
    correspondente. Sem isso, o voltar do sistema sai da rota com ela aberta.
    Nunca chame `history.pushState` direto; para sair da rota com camada
    aberta, use `sairDaRota(url)`, que não deixa entrada morta.
16. **O gesto nunca responde, pula nem conclui.** Ele só faz o que um botão
    visível ao lado já faz: questão não respondida não avança, a última do
    estudo não encerra (`registrarSessao` é irreversível) e a última da
    revisão do simulado não troca de tela.
17. **A pinça (zoom) nunca é desligada:** nada de `touch-action: pan-y` (ou
    `none`) nas áreas de leitura. A exceção é a `BarraAcao` com `onPuxar`,
    que não é área de leitura.
18. **Nada de `transform` nem `will-change` persistente no envoltório da
    questão:** o zoom da figura é `position: fixed` lá dentro, e um transform
    vira o bloco de contenção dele. O `deslizarQuestoes` limpa o transform ao
    soltar; o `in:fly` só existe durante a animação.

## Padrões de código

### Svelte / JS

- **Svelte 5, só com runes:**
  - Use `$state`, `$derived`/`$derived.by`, `$effect` com cleanup, `$props`
    com defaults, `$bindable` e `{@render children()}`.
  - Eventos vão como atributo: `onclick`, `<svelte:window onkeydown>`.
  - Nada de `on:click`, `export let`, `$:`, `<slot>` ou
    `createEventDispatcher`.
  - Estado compartilhado é um objeto `$state` exportado de um `.svelte.js`
    (ver `foco.svelte.js`).
  - Comportamento de DOM reaproveitável vai em attachment (`{@attach}`, a
    partir do Svelte 5.29), com o estado passado como FUNÇÃO lida na hora
    do evento (ver `deslizarQuestoes`). Passar o valor direto refaz o
    attachment a cada mudança.
  - O `+layout.svelte` e o treino leem a URL com `$page` de `$app/stores`,
    que é legado desde o Kit 2.12. Em código novo, prefira `page` de
    `$app/state`, e não misture os dois no mesmo arquivo.
- **Estilo:** tabs, aspas simples, ponto e vírgula e JS puro (sem
  TypeScript). Todo export novo leva JSDoc `/** */`; vários exports antigos
  ainda não têm, então complete quando mexer neles.
- **Nomes em português:**
  - funções no infinitivo (`carregarBanco`, `montarProva`,
    `registrarResposta`);
  - constantes em `UPPER_SNAKE` (`VERSAO_BANCO`, `TTL_CACHE_MS`);
  - props de callback `onX` (`onResponder`, `onMarcar`). O `aoFechar` do
    `SessaoTopo` é exceção antiga: não copie;
  - handlers locais `aoX` (`aoResponder`, `aoTecla`);
  - modais de confirmação `confirmaX`, outros overlays `xAberto`;
  - o prefixo `get*` é legado.
- **Comentários explicam o PORQUÊ** e, quando existe, citam o incidente real
  que a regra evita ("o aluno via a questão antiga por até 6 h"). Maiúsculas
  dão ênfase. Não comente o óbvio.
- **Modais:** backdrop `<button aria-label>`, `role="dialog" aria-modal
  aria-labelledby` e foco inicial no botão seguro.

### Visual

- **Mobile-first, com referência de 390 px.** No desktop, a nav fica no topo
  e a home tem 2 colunas; o quiz continua em uma coluna de leitura.
- **Só design tokens de `app.css`:**
  - Os principais: `bg-paper`, `bg-card`, `bg-tile`, `bg-panel`,
    `border-line`, `bg-bar`, `text-ink`, `text-ink-soft`, `accent*`, `ok-*`,
    `bad-*`, `warn-*`. Para botões, `btn3d` + `duo-accent`/`duo-btn`.
  - **Nunca use `dark:` nas telas:** o `.dark` troca os tokens sozinho.
  - Exceções que já estão em uso: `text-white` e `bg-white/N` sobre as faixas
    `bg-bar` e o botão vermelho, `bg-black/50` no backdrop de modal e âmbar
    no estado "parcial".
- **Token novo entra em três lugares de `app.css`:** `--color-<nome>:
  var(--<nome>)` em `@theme inline`, o valor claro em `:root` e o escuro em
  `.dark`.
  - Não há script de contraste no repo: calcule a razão AA (≥ 4,5:1 para
    texto) nos dois temas.
  - Uma troca de paleta também precisa alcançar o que está fora dos tokens:
    o `theme-color` do `app.html`, as sombras `rgba(20,33,61,…)` (estão nas
    rotas e no `Questao.svelte`: procure em todo o `src/`) e as texturas
    `.dotgrid`/`.pauta`/`.blueprint`.
- **Direção visual:** "papel de prova + caneta vermelha".
  - Fontes: Archivo (`font-display`, títulos e números), Plus Jakarta Sans
    (padrão do `body`) e JetBrains Mono (`font-code`). Outfit continua
    importada como fallback do display: não a remova sem tirar o fallback.
  - Títulos usam `text-hero/title/heading`, e etiquetas mono usam
    `text-label`. Texto corrido usa as classes do Tailwind; evite criar
    `text-[NNpx]` novo.
  - Ícones `phosphor-svelte` com `weight="bold"` e `aria-hidden="true"`. O
    `weight="fill"` fica para Play/Pause, troféu, raio do XP e estados ligados.
    Zero emoji.
- **Motion respeita `prefers-reduced-motion`:**
  - O CSS é zerado por uma media query global em `app.css`.
  - Transições Svelte e scroll suave **não** passam por ela. Use as
    constantes de `motion.js`: `DUR` (duração de `in:fly` etc.), `REDUCED`
    (`scrollIntoView`) e `reduzirMovimento()` (lê a preferência ao vivo).
- **Acessibilidade:**
  - Alvos de toque com no mínimo 44 px (`min-h-11`, ou `h-11 w-11` em botão
    só de ícone).
  - `role="status"`/`aria-live` nos avisos e `role="alert"` nos erros.

### Python (`banco/`)

- **Dependências:** os scripts sem PDF (`validar`, `testes`, `versao`,
  `digita`, `paragrafo`, `classificar --banco`, `geradas`) usam só a
  biblioteca padrão, e assim devem continuar. A extração usa Pillow e
  binários externos.
- **Estilo:** 4 espaços, aspas simples, sem anotação de tipo.
- **Estrutura:**
  - docstring de módulo com o porquê e a linha de uso (`python3 banco/x.py`);
  - `def main():` devolvendo 0/1 + `sys.exit(main())` (os scripts com
    `--banco` chamam `sys.exit(reaplicar_banco())`);
  - caminhos derivados de `__file__`, como no `versao.py`. Os scripts da
    extração têm `/root/...` fixo: não sirvem de modelo.
- **JSON:** `open(..., 'w', encoding='utf-8', newline='\n')` +
  `json.dump(..., ensure_ascii=False, indent=1)` + `\n` final. O `gerar.py` e
  o `versao.py` ainda omitem o `newline`; nunca o omita em código novo.
- **Exceções por id, nunca heurística nova** que possa mexer em questão boa
  (`FORA`, `SUBSTITUIR_TUDO`, `CORRECOES`).
- **Gravação defensiva:** confira tudo antes de gravar, e não grave nada se
  algo foi recusado.

## Como verificar uma mudança

- **Site:**
  - Rode `npm run build` (pega erro de SSR/prerender), depois `npm run
    preview`.
  - Olhe a tela em 390 px, no tema escuro e com movimento reduzido. Não pode
    haver rolagem lateral no celular.
  - Se a mudança mexe em rota, link ou página de erro, confira também o
    `app/build` com `servidor-404.py`.
- **Banco:** `validar.py` e `testes.py` limpos, e `versao.py --escrever`.
- **Antes do merge:** conferir a prévia da Vercel no celular.

## Git e PRs

- **Branch:** curta, criada a partir da `main` atualizada. Nome em kebab-case,
  em português e sem prefixo (`simulado-cronometrado`, `correcoes-banco`).
- **Commit:** `<área>: <resumo em minúsculas>`, com ` — <consequência>` quando
  couber.
  - Exemplos: `banco: versão na URL do JSON — deploy novo não serve mais o
    banco velho` e `simulado: prova de 2026 cronometrada, com correção só na
    entrega`.
  - Áreas usadas: `banco`, `simulado`, `estudo`, `treino`, `deploy`, `nav`,
    `mobile`, `design`, `ocr`, `testes`.
  - O corpo, quebrado em ~72 colunas, explica o porquê, o sintoma que o aluno
    via e os números de antes e depois.
- **PR:**
  - Título: o do commit, se houver um só; com vários commits, um resumo no
    mesmo formato.
  - Corpo em português, com `## O que muda`, `## Código` e `## Testes`. Os
    testes vão em checkboxes, com o que rodou e a saída, incluindo "conferir
    a prévia da Vercel no celular".
  - `## Antes de mergear` e `## Fora deste PR` entram quando houver pendência
    ou achado fora do escopo.
  - O merge é por merge commit, sem squash.
- **O que não vai para o git:**
  - O `.gitignore` cobre `node_modules/`, `app/build/`, `app/.svelte-kit/`,
    `__pycache__/`, `*.pyc`, `revisao/img/` e `*.txt` (em qualquer pasta).
  - `.claude/`, `.vercel/` e `.env` **não** estão nele. Adicione arquivos pelo
    nome, nunca com `git add .` ou `-A`.
- **Escopo e prioridades:** `ROADMAP.md` e `PLANO.md`.

## Docs desatualizados (aqui o código manda)

- **`README.md`:**
  - Chama `banco/` de "(futuro) scripts de extração", mas os scripts existem
    e estão em uso.
  - Descreve o fluxo "lote revisado antes de virar JSON". Hoje o `gerar.py`
    grava os dois juntos.
  - Diz "um ano na borda" para o cache do banco. Os JSON têm `s-maxage` de
    1 dia; um ano vale só para `/banco/img`.
- **`README.md` e `PLANO.md`:** citam `pdftoppm -r 150` e "foto → JPG q82".
  O código recorta a 200 dpi e o banco só usa PNG (`img/2019-FG-Q05.jpg` está
  órfão).
- **`PLANO.md` e `ROADMAP.md`:**
  - Falam em Outfit, "navy + laranja" e streak. Hoje é Archivo + Plus
    Jakarta, o acento é vermelho e o streak foi removido.
  - "Anulada = ponto para todos" não vale no simulado.
  - O `ROADMAP.md` cita um "preview LAN :8123" que não existe e deixa o
    deploy em aberto, mas o site já está no ar.
- **`banco.js`:** o comentário de `VERSAO_BANCO` manda "Bumpe a cada deploy",
  como se fosse à mão; use o `versao.py --escrever`. O arquivo também fala em
  "8 arquivos", mas são 9.
- **`revisao/`:** os `lote-*.md` e o `pendencias.md` são registro histórico
  da extração (falam em `materia_ava` e em "158 de 159"). Os modos `--banco`
  não os regeneram, e eles não servem como fonte de verdade.
- **`testes-mob/mob.js`:** ainda procura os níveis antigos "N1" do Estudo,
  não cobre o simulado e tem caminhos fixos de uma máquina Linux (Chromium em
  `/root/...`, base `http://127.0.0.1:8123`). Atualize antes de confiar nele.
