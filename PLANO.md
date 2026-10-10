# Direção do produto (10/10/2026, dono)

**É uma versão de ESTUDO para o simulado, focada nas questões das matérias
do AVA.** Cada questão carrega `materia_ava` (qual matéria do AVA estudar
para acertá-la). Questão sem correspondência direta fica com `null`
(= Formação Geral transversal).

## Modos

- **Treino livre** — fila infinita, filtro por tema, para quando quiser.
- **Estudo · 10 questões** — N1/N2/N3 por dificuldade (definida na revisão).
- **Simulado real** — FG 15 + CE 30 + 1 disc, 4h (abre com o banco completo).

## Linguagem visual e motion (inspirado no Duolingo, sem personagens)

- Botões primários 3D (borda inferior que afunda no press), XP flutuante
  "+10", chama com flicker no streak, shake no erro, pop no acerto,
  count-up no placar, transições de questão. Tudo respeita
  `prefers-reduced-motion`.
- **Modo escuro** de primeira classe (toggle no header, lembra a escolha,
  começa no `prefers-color-scheme`). Tokens semânticos em `app.css` viram
  sozinhos (`.dark`); contraste AA verificado por cálculo nos dois temas.
- Ícones Phosphor peso bold, zero emoji. Fonte Outfit + JetBrains Mono.

## Regras do banco (`app/static/banco/*.json`)

- `id, edicao, parte, numero, tipo, tema, dificuldade, materia_ava`,
  `enunciado, alternativas, gabarito | padrao`,
  `imagem {src, alt} | figura {desc, status}`.
- Figura = crop da página renderizada (`pdftoppm -r 150` + PIL), validada
  a olho antes de entrar. Fotos → JPG q82; linha → PNG optimize.
- Anulada (`gabarito: "ANULADA"`) = ponto para todos, como o INEP.
