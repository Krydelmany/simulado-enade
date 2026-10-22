// Exportar tabela em CSV para o professor levar à coordenação (P4).
//
// Formato pensado para o Excel em português, que é onde o arquivo vai abrir:
// separador `;` (com `,` o Excel pt-BR põe tudo numa coluna só, porque a
// vírgula é o separador decimal), BOM UTF-8 (sem ele os acentos viram "Ã§")
// e quebra de linha CRLF.

function celula(v) {
	if (v == null) return '';
	const s = String(v);
	return /[";\r\n]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s;
}

/**
 * Monta o texto do CSV.
 * @param {string[]} cabecalho
 * @param {Array<Array<unknown>>} linhas
 */
export function montarCsv(cabecalho, linhas) {
	return [cabecalho, ...linhas].map((l) => l.map(celula).join(';')).join('\r\n') + '\r\n';
}

/**
 * Baixa o CSV no navegador. Só chamar em handler de clique (usa `document`).
 * @param {string} nome nome do arquivo, sem extensão
 * @param {string[]} cabecalho
 * @param {Array<Array<unknown>>} linhas
 */
export function baixarCsv(nome, cabecalho, linhas) {
	const blob = new Blob(['﻿', montarCsv(cabecalho, linhas)], { type: 'text/csv;charset=utf-8' });
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = `${nome.replace(/[^\p{L}\p{N} _-]+/gu, '').trim() || 'painel'}.csv`;
	document.body.append(a);
	a.click();
	a.remove();
	setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** 2026-10-22T13:05:00Z → "22/10/2026" (vazio se não houver data). */
export function dataCsv(iso) {
	if (!iso) return '';
	const d = new Date(iso);
	return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString('pt-BR');
}
