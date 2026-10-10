# Roadmap — Simulado ENADE (atualizado 10/10/2026)

## Feito ✓

- [x] Formato real 2026 (Portaria INEP nº 161: FG 15 + CE 30 + 1 disc, 4h)
- [x] Coleta: 2014/2017/2019/2023 + gabaritos + padrões (143 obj + 17 disc)
- [x] Lote 1 (2019 FG) 100%: texto limpo, 4 figuras, tema/dificuldade/materia_ava
- [x] Template SvelteKit estático + banco JSON + preview LAN (`:8123`)
- [x] Design system: Outfit/Jakarta/JetBrains, navy + laranja, Phosphor, dark mode
- [x] Motion duo + auditoria a11y (14 achados corrigidos, contraste AA)
- [x] Port do Sleek (tab bar, header de sessão, CTA fixo, resumo, revisar erros)
- [x] QA mobile real (Chrome CDP + Pixel 7: overflow zero, fluxos fotografados)

## Agora → VISUAL LOCK (antes de qualquer feature nova)

- [x] **Desktop de verdade**: tab bar só no mobile, nav no topo, home 2 colunas + cartão-resposta, rodapé completo; quiz em coluna única (padrão)
- [x] **Direção própria**: papel de prova + caneta vermelha, Archivo Black, bolhas de cartão-resposta
- [ ] Dono aprova o visual (mobile + desktop) — **trava aqui**

## Depois do lock

- [ ] Lotes 2–4 no banco (2019 CE, 2023, 2014; 2017 precisa OCR parcial)
- [ ] Modo por matéria do AVA (filtro usando `materia_ava`)
- [ ] Simulado cronometrado (abre com banco completo)
- [ ] Repo GitHub + deploy Vercel + link p/ turma

## Fase 2 (só se a turma pedir)

- [ ] Backend p/ placar compartilhado (hoje é localStorage = por aparelho)
- [ ] PWA (instalar no celular, offline)
- [ ] Revisão espaçada de verdade
