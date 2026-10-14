# Roadmap — Simulado ENADE (atualizado 14/10/2026)

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

- [x] Lotes 2–4 no banco: as 160 questões oficiais, texto conferido com o PDF (`banco/digitadas.json`)
- [x] Matérias da Portaria nº 161 (20 áreas do CE) + filtro por matéria no Treino e no Estudo
- [x] Níveis Fácil/Médio/Difícil com 180 questões geradas para revisão; oficiais na categoria ENADE
- [x] Simulado cronometrado: 15 FG + 30 CE + 1 discursiva em 4 h, sorteio por matéria, cartão-resposta, pausa, correção na entrega
- [ ] Repo GitHub + deploy Vercel + link p/ turma

## Fase 2 (só se a turma pedir)

- [ ] Backend p/ placar compartilhado (hoje é localStorage = por aparelho)
- [ ] PWA (instalar no celular, offline)
- [ ] Revisão espaçada de verdade
