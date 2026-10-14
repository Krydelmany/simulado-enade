import { ehGerada } from './banco.js';
import { nomeMateria } from './materias.js';

/**
 * Copiar uma questão inteira para colar fora do site (Docs, Word, e-mail,
 * caderno de estudo): cabeçalho, enunciado, figura e alternativas.
 *
 * Vão dois formatos na mesma cópia, e quem cola escolhe o que entende:
 *  - `text/html`, com a figura EMBUTIDA como data URL — colar no Docs ou no
 *    Word traz a imagem junto, sem depender do site estar no ar;
 *  - `text/plain`, para onde só aceita texto (WhatsApp, bloco de notas). Ali
 *    a figura vira "[Figura: <descrição>]".
 *
 * Gabarito e padrão de resposta NÃO entram: é a questão, não a correção.
 */

const LETRAS = ['A', 'B', 'C', 'D', 'E'];
// IDÊNTICO ao `FENCE` do `TextoRico.svelte` e ao `FENCE_RENDER` do
// `validar.py` (ver "Blocos de código" no AGENTS.md)
const FENCE = /```([^\n`]*)\n?([\s\S]*?)```/g;
const LINK = /(https?:\/\/[^\s<>]+)/g;

function cabecalho(q) {
	if (ehGerada(q)) {
		const nivel = q.dificuldade === 'Média' ? 'Médio' : q.dificuldade;
		return `Questão de revisão ${q.id} · ${nivel}`;
	}
	const parte = q.parte === 'FG' ? 'Formação Geral' : 'Componente Específico';
	const n = Number(q.numero) || q.numero;
	const tipo = q.tipo === 'discursiva' ? 'Questão discursiva' : 'Questão';
	return `ENADE ${q.edicao} · ${parte} · ${tipo} ${n}`;
}

function subtitulo(q) {
	return [q.tema, q.materia ? nomeMateria(q.materia) : null].filter(Boolean).join(' · ');
}

// o banco guarda fontes como <https://…>
function semColchetes(t) {
	return (t || '').replace(/<(https?:\/\/[^<>\s]+)>/g, '$1');
}

/** Texto do banco em pedaços de texto corrido e de código (```lang … ```). */
function partes(t) {
	const limpo = semColchetes(t);
	const out = [];
	let ultimo = 0;
	let m;
	FENCE.lastIndex = 0;
	while ((m = FENCE.exec(limpo)) !== null) {
		if (m.index > ultimo) out.push({ codigo: false, valor: limpo.slice(ultimo, m.index) });
		out.push({ codigo: true, valor: m[2].replace(/\n$/, '') });
		ultimo = m.index + m[0].length;
	}
	if (ultimo < limpo.length) out.push({ codigo: false, valor: limpo.slice(ultimo) });
	return out;
}

function textoPlano(t) {
	return partes(t)
		.map((p) => (p.codigo ? `\n${p.valor}\n` : p.valor))
		.join('')
		.replace(/\n{3,}/g, '\n\n')
		.trim();
}

function esc(s) {
	return String(s)
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;');
}

function comLinks(s) {
	return s
		.split(LINK)
		.map((p, k) => (k % 2 ? `<a href="${esc(p)}">${esc(p)}</a>` : esc(p)))
		.join('');
}

const ESTILO_CODIGO =
	'font-family:Consolas,Menlo,monospace;font-size:13px;white-space:pre-wrap;' +
	'background:#f4f4f4;padding:8px 10px;border-radius:6px;margin:6px 0;';

function htmlDe(t) {
	return partes(t)
		.map((p) => {
			if (p.codigo) return `<pre style="${ESTILO_CODIGO}">${esc(p.valor)}</pre>`;
			return p.valor
				.split(/\n{2,}/)
				.map((par) => par.trim())
				.filter(Boolean)
				.map((par) => `<p style="margin:0 0 8px">${par.split('\n').map(comLinks).join('<br>')}</p>`)
				.join('');
		})
		.join('');
}

function alternativas(q) {
	if (q.tipo !== 'objetiva') return [];
	return LETRAS.filter((l) => q.alternativas?.[l]).map((l) => [l, q.alternativas[l]]);
}

/**
 * A questão em texto puro.
 * @param {object} q questão do banco
 * @returns {string}
 */
export function questaoEmTexto(q) {
	const linhas = [cabecalho(q)];
	const sub = subtitulo(q);
	if (sub) linhas.push(sub);
	linhas.push('');
	if (q.imagem) linhas.push(`[Figura: ${q.imagem.alt}]`, '');
	linhas.push(textoPlano(q.enunciado));
	if (q.tipo === 'objetiva' && q.alternativas_visuais) {
		linhas.push('', 'As alternativas A a E estão na figura.');
	}
	const alts = alternativas(q);
	if (alts.length) {
		linhas.push('');
		for (const [l, t] of alts) linhas.push(`${l}) ${textoPlano(t)}`);
	}
	return linhas.join('\n');
}

// a figura vira data URL para viajar dentro do HTML colado; se o download
// falhar, cai no endereço absoluto (funciona onde o colar busca a imagem)
async function srcDaFigura(src) {
	const absoluto = new URL(src, location.origin).href;
	try {
		const r = await fetch(absoluto);
		if (!r.ok) return absoluto;
		const blob = await r.blob();
		return await new Promise((ok, falha) => {
			const leitor = new FileReader();
			leitor.onload = () => ok(String(leitor.result));
			leitor.onerror = falha;
			leitor.readAsDataURL(blob);
		});
	} catch {
		return absoluto;
	}
}

/**
 * A questão em HTML, com a figura embutida.
 * @param {object} q questão do banco
 * @returns {Promise<string>}
 */
export async function questaoEmHtml(q) {
	const h = [`<p style="margin:0 0 4px"><strong>${esc(cabecalho(q))}</strong></p>`];
	const sub = subtitulo(q);
	if (sub) h.push(`<p style="margin:0 0 10px;color:#555">${esc(sub)}</p>`);
	if (q.imagem) {
		const src = await srcDaFigura(q.imagem.src);
		h.push(
			`<p style="margin:0 0 10px"><img src="${esc(src)}" alt="${esc(q.imagem.alt)}" style="max-width:100%;height:auto"></p>`
		);
	}
	h.push(htmlDe(q.enunciado));
	if (q.tipo === 'objetiva' && q.alternativas_visuais) {
		h.push('<p style="margin:0 0 8px"><em>As alternativas A a E estão na figura.</em></p>');
	}
	for (const [l, t] of alternativas(q)) {
		const corpo = t.includes('```') ? htmlDe(t) : comLinks(t.trim()).replace(/\n/g, '<br>');
		h.push(`<div style="margin:0 0 6px"><strong>${l})</strong> ${corpo}</div>`);
	}
	return `<div>${h.join('')}</div>`;
}

/**
 * Copia a questão para a área de transferência (HTML com figura + texto).
 * Chame direto do clique: o Safari só aceita a escrita dentro do gesto, por
 * isso o HTML vai como Promise no `ClipboardItem` em vez de ser esperado antes.
 *
 * @param {object} q questão do banco
 * @returns {Promise<boolean>} se copiou
 */
export async function copiarQuestao(q) {
	const texto = questaoEmTexto(q);
	try {
		if (navigator.clipboard?.write && typeof ClipboardItem !== 'undefined') {
			await navigator.clipboard.write([
				new ClipboardItem({
					'text/html': questaoEmHtml(q).then((h) => new Blob([h], { type: 'text/html' })),
					'text/plain': new Blob([texto], { type: 'text/plain' })
				})
			]);
			return true;
		}
	} catch {
		// navegador sem suporte a HTML na cópia: tenta só o texto
	}
	try {
		await navigator.clipboard.writeText(texto);
		return true;
	} catch {
		return false;
	}
}
