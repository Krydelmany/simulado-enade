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
5. Questão `ANULADA` no gabarito (`"gabarito": "ANULADA"`) = ponto p/ todos,
   como faz o INEP.

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
