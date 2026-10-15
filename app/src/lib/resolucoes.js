import { urlBanco } from './banco.js';

/**
 * Resoluções ("como resolver") das questões, com autor e auditoria.
 *
 * Ficam num arquivo À PARTE (`/banco/resolucoes.json`), fora de
 * `ARQUIVOS_BANCO`: são quase do tamanho do banco inteiro, e a home e o
 * início das sessões não precisam delas. O arquivo só é baixado quando a
 * primeira resolução vai aparecer (depois da primeira resposta), uma vez
 * por página. O `?v=` vem de `urlBanco`: o `versao.py` inclui este arquivo
 * no hash, então resolução nova não fica presa no cache do navegador.
 *
 * Formato: `{ "<id>": { texto, autor, auditado } }`, gerado por
 * `banco/resolucoes.py` a partir de `banco/resolucoes/*.json`.
 */

const ARQUIVO = 'resolucoes.json';

let promessa = null;

/**
 * Mapa id → resolução. Uma falha de rede devolve `{}` e libera nova
 * tentativa na próxima chamada.
 * @returns {Promise<Record<string, {texto: string, autor: string, auditado: boolean}>>}
 */
export function carregarResolucoes() {
	if (!promessa) {
		promessa = fetch(urlBanco(ARQUIVO))
			.then((r) => {
				if (!r.ok) throw new Error(`HTTP ${r.status}`);
				return r.json();
			})
			.catch(() => {
				promessa = null;
				return {};
			});
	}
	return promessa;
}

/**
 * Rótulo de autoria do topo do bloco: "IA · Não auditado".
 * @param {{autor?: string, auditado?: boolean}} r
 */
export function rotuloAutoria(r) {
	return `${r?.autor || 'IA'} · ${r?.auditado ? 'Auditado' : 'Não auditado'}`;
}
