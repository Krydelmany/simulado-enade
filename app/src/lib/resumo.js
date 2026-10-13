// Fachada de LEITURA para a UI (home e resumo de sessão).
//
// PORQUÊ existir: as telas não devem agregar nem formatar números — só
// desenhar. Tudo aqui é calculado a partir de `stats.js` (que lê o
// `localStorage`) e sai pronto para render: quantidades já em pt-BR, listas já
// ordenadas por utilidade.
//
// Este módulo é puro em relação ao SvelteKit (nada de `$app/*`), então roda
// igual em Node nos testes. `resumoProgresso()` não muta nada.

import {
	getErros,
	carregarSessao,
	formatarNumero,
	resumo as resumoBruto
} from './stats.js';

export { formatarNumero };

const DIAS_SEMANA = ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'];

function percentual(fracao) {
	const v = Number.isFinite(fracao) ? Math.round(fracao * 100) : 0;
	return `${formatarNumero(v)}%`;
}

/** `'2026-10-06'` -> `'seg 06/10'` (rótulo curto para o gráfico de 7 dias). */
function rotuloDia(iso) {
	const [ano, mes, dia] = iso.split('-');
	const dow = new Date(Number(ano), Number(mes) - 1, Number(dia)).getDay();
	return `${DIAS_SEMANA[dow]} ${dia}/${mes}`;
}

function dataHora(ms) {
	const d = new Date(ms);
	const p = (n) => String(n).padStart(2, '0');
	return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

function relativo(ms) {
	const dias = Math.floor((Date.now() - ms) / 86_400_000);
	if (dias <= 0) return 'hoje';
	if (dias === 1) return 'ontem';
	if (dias < 7) return `há ${dias} dias`;
	if (dias < 30) return `há ${Math.floor(dias / 7)} sem`;
	if (dias < 365) return `há ${Math.floor(dias / 30)} meses`;
	return `há ${Math.floor(dias / 365)} ano(s)`;
}

/** Normaliza uma linha de `porMateria`/`porTema` para exibição. */
function linhaGrupo(g) {
	return {
		nome: g.nome,
		respondidas: formatarNumero(g.respondidas),
		respondidasNumero: g.respondidas,
		acertos: formatarNumero(g.acertos),
		acertosNumero: g.acertos,
		erros: formatarNumero(g.erros),
		errosNumero: g.erros,
		precisao: percentual(g.precisao),
		precisaoNumero: g.precisao
	};
}

/**
 * Retrato completo do progresso, formatado e ordenado, pronto para a UI.
 *
 * Campos (os `*Numero` são os valores crus, para cálculo/ordenação na tela):
 *  - `xp` (string) / `xpNumero` — XP acumulado.
 *  - `respondidas`, `certas` (strings) / `*Numero` — totais de vida inteira.
 *  - `precisao` (string `"78%"`) / `precisaoNumero` (0..1).
 *  - `porMateria`, `porTema`: `[{ nome, respondidas, respondidasNumero, acertos,
 *    acertosNumero, erros, errosNumero, precisao, precisaoNumero }]`, ordenado
 *    por volume de respostas (desc) e, no empate, pela pior precisão primeiro.
 *  - `erros`: array de ids de questões ainda erradas (ordem de inserção).
 *  - `totalErros` / `totalErrosNumero`.
 *  - `ultimoTreino` (string `"12/10/2026 14:30"`) / `ultimoTreinoEm` (ms|null) /
 *    `ultimoTreinoRelativo` (`"há 2 dias"`). `null` se nunca treinou.
 *  - `sessaoPausada`: `null` ou `{ modo, i, total, respondidas, certas, tema,
 *    progresso, inicioEm, xpGanho }` — a sessão salva para "continuar depois".
 *  - `dias`: 7 entradas (mais antiga -> hoje), cada uma `{ dia, rotulo,
 *    respondidas, respondidasNumero, certas, precisao, precisaoNumero, ehHoje }`.
 *  - `hoje`: `{ dia, respondidas, certas, parciais }` (cru).
 *  - `ultimos7`: `{ respondidas, certas, precisao }` (cru).
 *  - `temDados`: `true` se já houve alguma resposta registrada.
 *
 * @returns {object} o retrato acima.
 */
export function resumoProgresso() {
	const r = resumoBruto();
	const erros = getErros();
	const bruta = carregarSessao();

	const sessaoPausada = bruta
		? {
				modo: 'treino',
				i: Number(bruta.i) || 0,
				total: Array.isArray(bruta.ids) ? bruta.ids.length : 0,
				respondidas: formatarNumero(bruta.feitas ?? 0),
				certas: formatarNumero(bruta.certas ?? 0),
				tema: bruta.tema ?? 'todos',
				progresso: `${formatarNumero((Number(bruta.i) || 0) + 1)} / ${formatarNumero(
					Array.isArray(bruta.ids) ? bruta.ids.length : 0
				)}`,
				inicioEm: Number(bruta.inicio) || null,
				xpGanho: formatarNumero(bruta.xpGanho ?? 0)
			}
		: null;

	return {
		xp: formatarNumero(r.xp),
		xpNumero: r.xp,
		respondidas: formatarNumero(r.respondidas),
		respondidasNumero: r.respondidas,
		certas: formatarNumero(r.certas),
		certasNumero: r.certas,
		precisao: percentual(r.precisao),
		precisaoNumero: r.precisao,
		porMateria: r.porMateria.map(linhaGrupo),
		porTema: r.porTema.map(linhaGrupo),
		erros: erros.slice(),
		totalErros: formatarNumero(erros.length),
		totalErrosNumero: erros.length,
		ultimoTreino: r.ultimoTreino ? dataHora(r.ultimoTreino) : null,
		ultimoTreinoEm: r.ultimoTreino,
		ultimoTreinoRelativo: r.ultimoTreino ? relativo(r.ultimoTreino) : null,
		sessaoPausada,
		dias: r.dias.map((d) => ({
			dia: d.dia,
			rotulo: rotuloDia(d.dia),
			respondidas: formatarNumero(d.respondidas),
			respondidasNumero: d.respondidas,
			certas: formatarNumero(d.certas),
			precisao: percentual(d.respondidas > 0 ? d.certas / d.respondidas : 0),
			precisaoNumero: d.respondidas > 0 ? d.certas / d.respondidas : 0,
			ehHoje: d.dia === r.hoje.dia
		})),
		hoje: r.hoje,
		ultimos7: r.ultimos7,
		temDados: r.respondidas > 0
	};
}
