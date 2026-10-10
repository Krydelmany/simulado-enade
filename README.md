# Simulado ENADE — Engenharia de Computação

Site de simulado para a turma: treino livre, estudo em 10 questões com níveis
e simulado no formato real da prova (Portaria INEP nº 161/2026).

- `app/` — SvelteKit + Tailwind, build estático (deploy na Vercel)
- `app/static/banco/*.json` — banco de questões (única fonte de verdade do app)
- `fontes/` — PDFs oficiais (RIEP/INEP, GitHub geacc/enade) + relatório do professor
- `revisao/` — lotes de extração para aprovação antes de entrar no banco
- `banco/` — (futuro) scripts de extração
- `INVENTARIO.md` — o que cada edição tem
