# Simulado ENADE — Engenharia de Computação

Site de estudo para a prova do ENADE com questões oficiais do INEP:
**treino livre** (fila infinita), **estudo em sessões de 10 por matéria** —
questões de revisão em três níveis (Fácil, Médio, Difícil) ou a prova oficial
— e **simulado no formato real da prova** (Portaria INEP nº 161/2026:
FG 15 + CE 30 + 1 discursiva, 4h).

## Subir o projeto

Pré-requisitos: **Node 20+** (usamos o 22) + npm + Git.

```sh
git clone https://github.com/Krydelmany/simulado-enade.git
cd simulado-enade/app
npm install
npm run dev      # http://localhost:5173
```

Outros comandos (dentro de `app/`):

```sh
npm run build    # gera o site estático em app/build
npm run preview  # serve o build p/ conferir antes de publicar
```

## Publicar na Vercel

O app é SvelteKit com `adapter-static`, mas ele mora em `app/` — na raiz do
repositório não tem `package.json`, então a Vercel não acha o que buildar
sem saber onde o site está. Isso se configura **no painel**
(**Settings → Build and Deployment → Root Directory = `app`**); o
`vercel.json` não tem essa chave e a Vercel rejeita o arquivo se ela
aparecer lá.

1. Vercel → **Add New → Project** → importa `Krydelmany/simulado-enade`;
2. em **Root Directory**, pôr `app` (é o passo que não dá para pular);
3. cada push em `main` publica sozinho; cada PR ganha URL de preview.

O `app/vercel.json` (fica ao lado do `package.json` por causa do Root
Directory) cuida do resto: preset SvelteKit, comando de build e o cache do
banco de questões — `max-age=0` no browser para o aluno revalidar, um ano
na borda para o mundo não pedir de novo.

Sem servidor: o `adapter-static` cospe HTML puro, o plano grátis dá conta.
O `.vercelignore` segura os 20 MB dos PDFs do INEP fora do deploy — eles
são material de trabalho, não do site.

## Como o projeto está organizado

```
app/                  o site (SvelteKit 2 + Svelte 5 + Tailwind 4 + Vite 6)
  src/routes/         páginas: / (início), /treino, /estudo, /simulado
  src/lib/            Questao.svelte, SessaoTopo, BarraAcao, banco.js, stats.js…
  static/banco/       O BANCO: *.json de questões + img/ (única fonte do app)
  static/favicon.svg  marca
fontes/               PDFs oficiais (RIEP/INEP, GitHub geacc/enade) + relatório
revisao/              lotes de extração p/ aprovar antes de entrar no banco
banco/                (futuro) scripts de extração
testes-mob/           harness mobile: pilota Chromium emulado (Pixel 7),
                      fotografa fluxos e mede rolagem lateral
INVENTARIO.md         o que cada edição tem (143 objetivas + 17 discursivas)
PLANO.md              direção do produto · ROADMAP.md → fases e status
```

## Como entra questão nova no banco

1. A fonte vai em `fontes/` (prova + gabarito + padrão de resposta).
2. Extrai em lote de 10 para `revisao/lote-NN-<edicao>-<parte>.md` com:
   enunciado limpo, alternativas, gabarito, padrão da discursiva,
   `tema`, `dificuldade` (Fácil/Média/Difícil) e `materia` — o id de uma
   matéria de `app/src/lib/materias.json` (as 20 áreas do CE da Portaria
   nº 161/2026, ou uma das matérias de Formação Geral).
3. Alguém revisa o lote; só o aprovado vira JSON em
   `app/static/banco/*.json` no formato:
   `id, edicao, parte, numero, tipo, tema, dificuldade, materia,
   enunciado, alternativas, gabarito | padrao, imagem? {src, alt, legenda?}`.
   A classificação mora em `banco/classificacao.json`; para trocar a matéria
   ou o tema de uma questão sem reextrair a prova:
   `python3 banco/classificar.py --banco`.
4. Figura = recorte da página renderizada (`pdftoppm -r 150` + corte),
   validado a olho. Foto → JPG q82; linha/gráfico → PNG. Nada de baixar
   vídeo — vídeo é link, nunca arquivo (regra do projeto).
5. Questão `ANULADA` no gabarito (`"gabarito": "ANULADA"`) não vai para o
   site: `banco/anuladas.py` a separa em `banco/anuladas.json` (o `gerar.py`
   e o `digita.py --banco` fazem isso sozinhos).

## Questões geradas (níveis Fácil / Médio / Difícil)

Os três níveis do modo Estudo NÃO usam as questões do INEP — elas ficam
juntas na categoria **ENADE oficial**. Os níveis são de questões escritas
para revisão, 3 por nível em cada uma das 20 matérias do CE:

- **Fácil**: conceito direto, contexto de uma ou duas frases;
- **Médio**: aplicação — cenário curto, uma conta ou um traço de código;
- **Difícil**: o modelo da prova — texto-base com afirmações I/II/III ou
  asserção-razão (I PORQUE II).

A fonte é `banco/geradas/NN-<materia>.json` (só o conteúdo); o
`python3 banco/geradas.py` monta `app/static/banco/geradas.json` no mesmo
formato das oficiais, com `fonte: "gerada"` e id `GER-<inciso>-<F|M|D><n>`,
e escreve o markdown de revisão em `revisao/geradas/`. Questão nova entra no
FIM do arquivo da matéria — reordenar troca os ids e o histórico do aluno é
guardado por id. Depois, `validar.py` e `versao.py --escrever`, como sempre.

## Parágrafos e espaçamento do texto

O app desenha `\n` como quebra (`white-space: pre-line` no `.enunciado`),
então o JSON precisa trazer os parágrafos. Quem monta é o `banco/paragrafo.py`,
chamado pela `qualidade.limpa` na extração:

- **linhas do PDF → parágrafos** (`reflui`): linha cheia emenda com a de
  baixo; linha curta com ponto fecha parágrafo; linha curta sem ponto
  (tabela, código, título) fica sozinha; "•" sozinho junta com a linha
  seguinte;
- **estrutura da prova** (`estrutura`): fonte ("Disponível em", "SOBRENOME,
  X.") e comando ("Considerando…", "É correto…") em parágrafo próprio,
  afirmações I., II. e itens a), b) um por linha, `PORQUE` isolado, pergunta
  final sem ponto separada do texto-base;
- **só espaço em branco muda** — exceto a tabela `GRUDADAS` (palavras que o
  poppler colou em 2019) e o "•" da fonte Symbol (``, que o navegador
  mostra como quadradinho). Rótulo lido errado pelo OCR ("|." por "I.") NÃO
  é trocado aqui — "Il." pode ser II ou III; quem decide é a leitura da
  página, em `digitadas.json` (abaixo).

Para reaplicar no banco sem reextrair: `python3 banco/paragrafo.py --banco`
(confere texto visível e idempotência antes de gravar); casos de teste em
`python3 banco/testes.py`.

Regras de extração que já doeram:

- **rodapé do PDF** (`Área livre`, nº de página, `ENGENHARIA DE…`) vaza para
  o fim da última alternativa — cortar sempre;
- **`mod/resource` não existe aqui**; no AVA o scraping é só HTML (ver
  `INVENTARIO.md`);
- **2014 e 2017 têm fonte quebrada** (sem `ToUnicode`): o `pdftotext` devolve
  glifos trocados, e a página precisa ser RENDERIZADA para o tesseract ler.
  Renderizar com **mutool**, não com `pdftoppm` — a fonte substituída pelo
  poppler sai com glifos que o tesseract lê errado de forma sistemática
  (toda maiúscula vira minúscula);
- **depois de gerar, rode `python3 banco/versao.py --escrever`.** A versão
  do banco embutida em `banco.js` é o que invalida a cache do
  `sessionStorage`; sem isso o aluno vê o banco velho por até 6 horas sem
  nenhum sinal. O script deriva a versão do conteúdo, então não dá para
  esquecer;
- **`python3 banco/validar.py` precisa sair limpo.** Ele pega o que nenhuma
  tela acusa: alternativa repetida, gabarito fora das letras, imagem que não
  existe, `padrao` que é placeholder, lixo de página;
- **nada entra no banco sem passar em `banco/qualidade.py`.** Questão com
  alternativa faltando, enunciado vazado para dentro das alternativas ou
  gabarito fora das letras lidas fica de fora — com uma opção a menos, o
  gabarito aponta para a letra errada e o aluno erra sem saber por quê. O
  que sobrou está em `revisao/pendencias.md`.

## Texto lido do PDF (`banco/digitadas.json`)

Onde a extração não dá conta — OCR de 2014/2017, fórmula e figura achatadas
em 2019/2023, enunciado cortado — o texto é lido da página renderizada e
digitado em `banco/digitadas.json`, uma entrada por id:

- `A`…`E`: alternativas (com as cinco, as cinco substituem as da extração);
- `_enunciado` / `_padrao`: texto inteiro, já com parágrafos, listas e
  blocos ```` ``` ```` de código;
- `_imagem` `{src, alt}`: recorte da página (200 dpi) em
  `app/static/banco/img/`;
- `_alternativas_visuais: true`: as alternativas são desenho (gráfico,
  circuito) e vêm no recorte;
- `_nova` `{edicao, parte, numero, tipo, gabarito?, imagem?}`: questão que a
  extração nem produziu (2014-CE-D04, colada na D03 pelo OCR).

A regra é a do `digita.py`: **nunca preencher por dedução** — o que não deu
para ler fica de fora. A letra do gabarito vem sempre da folha oficial.

`digita.aplica` entra no começo da cadeia do `gerar.py` e `digita.finaliza`
no fim: `arruma`/`formato`/`qualidade` consertam camada de texto e OCR, e
passados sobre um texto já digitado desmontam bloco de código e indentação.
Para aplicar sem reextrair (sem poppler/tesseract):

```bash
python3 banco/digita.py --banco      # entra no JSON do site
python3 banco/paragrafo.py --banco   # tem de dizer "0 de N reformatadas"
python3 banco/validar.py && python3 banco/testes.py
python3 banco/versao.py --escrever
```

O `testes.py` passa cada entrada pela cadeia inteira do `gerar.py` e exige o
mesmo texto que está no banco.

Dois defeitos de extração que esse arquivo corrige e que valem conferir em
prova nova: em 2019/2023 a frase que começa com "A " ("A partir dessas
informações…", "A respeito dessas asserções…") era lida como a alternativa
A, e o que vinha depois dela — afirmações, código, a própria pergunta —
sumia; e alternativas deslocadas em uma letra, que mostram como certa a
opção errada sem nenhum sintoma (2014-CE-Q35, 2017-CE-Q35, 2023-CE-Q18).

## Convenções do código (seguir para não quebrar o visual)

- **Mobile-first, referência 390px.** Desktop se adapta (nav no topo, home
  em 2 colunas); quiz continua em coluna de leitura — é o padrão.
- **Design tokens em `app/src/app.css`** (`@theme inline`): `paper, card,
  tile, ink, accent…` — **nunca hex cru nas telas**; o `.dark` vira sozinho.
- **Animações** respeitam `prefers-reduced-motion` (`src/lib/motion.js`).
- **Contraste AA**: qualquer cor nova passa pelo cálculo antes (scripts
  usados estão no histórico; perguntar que eu mostro).
- Progresso do aluno fica no `localStorage` (por aparelho, sem login).
  Placar compartilhado = fase 2 com backend — ainda não existe.

## Fluxo de trabalho sugerido

`main` é o que está no ar. Mudança = branch curta + PR (a Vercel dá preview
automático) + merge após olhar no celular. Dúvida de escopo: `ROADMAP.md`.
