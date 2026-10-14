# Direção do produto (10/10/2026, dono)

**É uma versão de ESTUDO para o simulado, organizada por matéria.** Cada
questão carrega `materia`: uma das 20 áreas do Componente Específico da
Portaria INEP nº 161/2026 ou uma matéria de Formação Geral
(`app/src/lib/materias.json`). As matérias do AVA que tinham par na lista da
Portaria foram absorvidas por ela (ex.: TELECOMUNICACOES → Redes de
Computadores); as de FG sem par continuam como estavam. (13/10/2026)

## Modos

- **Treino livre** — fila infinita, filtro por matéria, para quando quiser.
- **Estudo · 10 questões** — filtro de matéria + quatro categorias:
  **Fácil / Médio / Difícil** (questões geradas para revisão, do contexto
  simples ao modelo da prova) e **ENADE oficial** (todas as do INEP).
- **Simulado real** — FG 15 + CE 30 + 1 disc, 4h: sorteio espalhado pelas matérias, cartão-resposta, pausa, correção só na entrega.

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

- `id, edicao, parte, numero, tipo, tema, dificuldade, materia`,
  `enunciado, alternativas, gabarito | padrao`,
  `imagem {src, alt} | figura {desc, status}`.
- Figura = crop da página renderizada (`pdftoppm -r 150` + PIL), validada
  a olho antes de entrar. Fotos → JPG q82; linha → PNG optimize.
- Anulada (`gabarito: "ANULADA"`) = ponto para todos, como o INEP.
