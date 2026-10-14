@AGENTS.md

# Notas para o Claude Code

O `AGENTS.md` importado acima é a fonte única sobre como o sistema funciona e
quais são as regras do projeto, e vale para qualquer agente. Este arquivo
guarda só o que é específico do Claude Code. Quando o sistema mudar,
atualize o `AGENTS.md`, não este arquivo.

- **Ambiente:** Windows, com Git Bash e PowerShell. Rode os scripts do banco a
  partir da raiz do repositório com `python -X utf8 banco/<script>.py`. Sem
  essa flag, os acentos viram `�` no console ou dão `UnicodeEncodeError`. A
  flag funciona nos dois shells. O prefixo `PYTHONIOENCODING=utf-8 python …`
  também resolve, mas só no Bash.
- **Preview do site:** a configuração `app-preview` fica em
  `.claude/launch.json`. O arquivo não é versionado e também não está no
  `.gitignore`, então nunca o adicione a um commit. Essa configuração roda o
  `vite preview` na porta 4173 a partir de `app/`.
  - O preview serve a saída do `npm run build` em `app/.svelte-kit/output`,
    não o `app/build`. Rode o build antes.
  - Se o `runtimeExecutable` apontar para um Node que não existe nesta
    máquina, troque pelo `C:\Program Files\nodejs\node.exe`.
  - Para o `npm run dev` (porta 5173), crie outra configuração.
  - Para ver exatamente o que vai para a Vercel, incluindo a página 404, use
    `python banco/servidor-404.py 8126 app/build`.
- **Verificação visual:** confira mudanças de tela no navegador do app, em
  390 × 844 (tamanho personalizado; o preset mobile tem 375 px), também no
  tema escuro, e procure rolagem lateral. Mostre a captura ao terminar.
- **Mudanças no banco:** antes de dizer que terminou, rode `validar.py`,
  `testes.py` e `versao.py --escrever` e informe a saída de cada um.
- **Commits e PRs:** siga o formato do `AGENTS.md`, em português. Só faça
  commit, push ou PR quando o usuário pedir. Use `gh` com
  `--repo Krydelmany/simulado-enade`.
- **PDFs de `fontes/`:** não leia os PDFs inteiros sem necessidade, porque
  somam uns 20 MB. Para conferir uma questão, comece pelo texto dela em
  `digitadas.json` e no JSON do banco. Para conferir um gabarito, use
  `pdftotext fontes/<ano>-e2_gabarito.pdf -` (no Git Bash). Em 2023, o
  arquivo é `fontes/2023-gabarito.pdf`, sem o `-e2_`.
