# Fase 1 — Inventário de fontes (2026-10-10)

Fontes em `fontes/`. Provas oficiais do INEP (RIEP + GitHub `geacc/enade`)
+ relatório do professor (AVA, via `ava-materiais`).

## Provas oficiais — Engenharia de Computação

| Edição | Formato | Objetivas | Discursivas | Gabarito | Padrão resp. | Anuladas | Extração de texto |
|---|---|---|---|---|---|---|---|
| 2014 | FG 1–8 + CE 9–35 | 35 | 5 (D1–D5) | ok | ok (9 p.) | Q27, Q30, Q34 | OCR (mutool + tesseract) — 19/39 no banco |
| 2017 | FG 1–8 + CE 9–35 | 35 | 5 (D1–D5) | ok | ok (11 p.) | — | OCR (mutool + tesseract) — 24/40 no banco |
| 2019 | FG 1–8 + CE 9–35 | 35 | 5 (D1–D5) | ok | ok (10 p.) | Q1 (= mesma do AVA) | pdftotext — 38/40 no banco |
| 2023 | FG 1–9 + CE 10–38 | 38 | 2 (D1–D2) | ok | ok | — | pdftotext — 40/40 no banco |

**Total: 143 objetivas + 17 discursivas = 160 questões.**
**No banco hoje: 123** (107 objetivas + 16 discursivas). O que falta está em
`revisao/pendencias.md`, com o motivo de cada uma — em geral o OCR da prova
perde a bolinha de uma alternativa e o gabario passaria a apontar para a
letra errada.

Anulada = o INEP credita a todos (como fez o professor no relatório:
"Q1 anulada no gabarito oficial: creditada a todos, como faz o INEP").

## Arquivos

```
fontes/
  2014-e1_prova.pdf / 2014-e2_gabarito.pdf / 2014-e3_padrao.pdf
  2017-e1_prova.pdf / 2017-e2_gabarito.pdf / 2017-e3_padrao.pdf
  2019-e1_prova.pdf / 2019-e2_gabarito.pdf / 2019-e3_padrao.pdf  (= AVA)
  2023-prova.pdf    / 2023-gabarito.pdf    / 2023-padrao.pdf     (RIEP/INEP)
  simulado-prof-2026.pdf   <- relatório de desempenho, NÃO é banco
```

## "Simulado Enade 2026" do professor — o que é de verdade

Relatório de 12 p. com o desempenho da turma (13 alunos) na prova 2019:
média 41,5%, 75% dos cruzamentos aluno×área abaixo de 50%. Não tem questões
novas — mas entrega duas coisas prontas:

1. **Taxonomia de 17 áreas** (usar como `tema` no banco): PDS, Eletrônica
   Digital/Circuitos Lógicos, IHC, Eletrônica Analógica, Matemática Aplicada
   e Estatística, Estrutura de Dados e Algoritmos, Segurança, Redes,
   Sistemas Distribuídos e IoT, Teoria da Computação, IA e ML, Eng. de
   Software, Banco de Dados, + Formação Geral.
2. **Onde a turma erra** (prioriza níveis/sessões de estudo): PDS 7,7%,
   Eletrônica Digital 11,5%, IHC 15,4%, Eletrônica Analógica 19,2%,
   Matemática/Estatística 23,1%. Fortes: Distribuídos/IoT 76,9%, Teoria
   69,2%, IA/ML 61,5%.

## Notas para a fase 2 (extração)

- Figuras são majoritariamente **vetoriais** (raster conta pouco:
  15/5/3/5 imgs). Extrair por crop da página renderizada, não por
  `pdfimages`.
- **2014 e 2017 exigem OCR.** A fonte embutida não tem `ToUnicode`, então o
  `pdftotext` devolve glifos trocados: a página é renderizada (com `mutool`,
  não `pdftoppm`) e lida pelo tesseract. O que o OCR não pega é a bolinha da
  alternativa — daí a busca por desenho na imagem (`ocr._bolinhas_da_imagem`)
  e a porta de qualidade que preferisce deixar a questão de fora.
- `Questionario_INEP_Enade_2026.pdf` (AVA) é o questionário
  socioeconômico — não pontua, **fora** do banco.
- Referência de formato 2026 (prova real que farão): Portaria INEP nº 161 —
  FG 15 objetivas + CE 30 objetivas + 1 discursiva, 4h
  (`/tmp/opencode/portaria161.txt`, PDF em `/tmp/opencode/portaria161.pdf`
  — **mover para cá** antes de limpar o /tmp).
