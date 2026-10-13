"""Servidor que imita a Vercel na parte que importa: rota inexistente cai no
`404.html` gerado pelo `adapter-static`, em vez de dar 404 cru.

O `python -m http.server` não faz isso — por isso a validação anterior
mostrou a página cinza do Python e não a do site. Aqui a gente confere o que
o aluno realmente veria ao digitar uma URL errada.

    python3 servidor-404.py 8126 app/build
"""

import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

RAIZ = sys.argv[2] if len(sys.argv) > 2 else 'app/build'
PORTA = int(sys.argv[1]) if len(sys.argv) > 1 else 8126


class Vercel(SimpleHTTPRequestHandler):
    """Estático + `404.html` como fallback, como a Vercel faz com SPA."""

    def send_head(self):
        caminho = self.translate_path(self.path)
        if self.path.endswith('/'):
            caminho += 'index.html'
        try:
            with open(caminho, 'rb'):
                return super().send_head()
        except OSError:
            pass
        # não achou: devolve o 404 do site, não o do Python
        self.path = '/404.html'
        return SimpleHTTPRequestHandler.send_head(self)

    def send_error(self, code, message=None, explain=None):
        if code == 404:
            self.path = '/404.html'
            self.send_head()
            self.wfile.write(b'')
            return
        SimpleHTTPRequestHandler.send_error(self, code, message, explain)

    def log_message(self, fmt, *a):
        pass


ThreadingHTTPServer(('127.0.0.1', PORTA), partial(Vercel, directory=RAIZ)).serve_forever()