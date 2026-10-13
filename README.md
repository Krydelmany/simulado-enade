# Simulado ENADE — Engenharia de Computação

Site de estudo para a prova do ENADE com questões oficiais do INEP:
**treino livre** (fila infinita), **estudo em 10 questões com níveis N1–N3**
e **simulado no formato real da prova** (Portaria INEP nº 161/2026:
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

O `vercel.json` já deixa tudo pronto: `rootDirectory: app`, preset SvelteKit,
comando de build e cache do banco de questões. Então:

1. Vercel → **Add New → Project** → importa `Krydelmany/simulado-enade`;
2. aceitar tudo que a Vercel detectar (não precisa mexer em Root Directory —
   o `vercel.json` já aponta para `app`);
3. cada push em `main` publica sozinho; cada PR ganha URL de preview.

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
   `tema`, `dificuldade` (Fácil/Média/Difícil) e `materia_ava`
   (qual matéria do AVA estudar — `null` se for FG transversal).
3. Alguém revisa o lote; só o aprovado vira JSON em
   `app/static/banco/*.json` no formato:
   `id, edicao, parte, numero, tipo, tema, dificuldade, materia_ava,
   enunciado, alternativas, gabarito | padrao, imagem? {src, alt, legenda?}`.
4. Figura = recorte da página renderizada (`pdftoppm -r 150` + corte),
   validado a olho. Foto → JPG q82; linha/gráfico → PNG. Nada de baixar
   vídeo — vídeo é link, nunca arquivo (regra do projeto).
5. Questão `ANULADA` no gabarito (`"gabarito": "ANULADA"`) = ponto p/ todos,
   como faz o INEP.

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
- **Zero emoji** — ícones `phosphor-svelte` peso `bold`, com `aria-hidden`
  quando decorativos.
- **Animações** respeitam `prefers-reduced-motion` (`src/lib/motion.js`).
- **Contraste AA**: qualquer cor nova passa pelo cálculo antes (scripts
  usados estão no histórico; perguntar que eu mostro).
- Progresso do aluno fica no `localStorage` (por aparelho, sem login).
  Placar compartilhado = fase 2 com backend — ainda não existe.

## Fluxo de trabalho sugerido

`main` é o que está no ar. Mudança = branch curta + PR (a Vercel dá preview
automático) + merge após olhar no celular. Dúvida de escopo: `ROADMAP.md`.
