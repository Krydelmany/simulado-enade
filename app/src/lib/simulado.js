// Simulado no formato da prova de 2026 — Portaria INEP nº 161, de 14/04/2026
// (Engenharia de Computação): Formação Geral com 15 objetivas, Componente
// Específico com 30 objetivas e 1 discursiva, em 4 horas.
//
// Aqui fica só a lógica (montar, corrigir, guardar). A tela mora em
// `routes/simulado/+page.svelte`; o relógio também, porque depende do DOM.

import { ehGerada, embaralhar } from './banco.js';

export const FORMATO = {
	fg: 15,
	ce: 30,
	discursivas: 1,
	duracaoMs: 4 * 60 * 60 * 1000
};
export const TOTAL_QUESTOES = FORMATO.fg + FORMATO.ce + FORMATO.discursivas;

const CHAVE = 'enade-simulado';
const CHAVE_ULTIMO = 'enade-simulado-ultimo';
// simulados da turma já entregues neste aparelho: {[id]: {em, certas, total}}.
// A prova entregue some de `enade-simulado` quando o aluno começa outra, e o
// cartão da turma não pode voltar a oferecer uma prova que ele já fez.
const CHAVE_TURMA = 'enade-simulados-turma';

// Anulada fica fora do sorteio: ponto de graça distorce a nota de quem está
// medindo o próprio preparo. Discursiva sem padrão publicado (só desenho)
// também — sem padrão não há com o que se autoavaliar.
function elegivel(q) {
	return !ehGerada(q) && q.gabarito !== 'ANULADA' && !q.padrao_placeholder;
}

/**
 * Sorteia `n` questões espalhando pelas matérias: uma de cada matéria por
 * rodada, até completar. Sorteio puro concentraria a prova nas matérias com
 * mais questões no banco (Algoritmos tem 12 objetivas de CE; Controle,
 * 3), e o simulado deixaria de cobrir a lista da Portaria.
 */
export function sortearBalanceado(lista, n) {
	const grupos = new Map();
	for (const q of embaralhar(lista)) {
		const k = q.materia || '?';
		if (!grupos.has(k)) grupos.set(k, []);
		grupos.get(k).push(q);
	}
	const filas = embaralhar([...grupos.values()]);
	const saida = [];
	while (saida.length < n && filas.some((f) => f.length)) {
		for (const f of filas) {
			if (saida.length >= n) break;
			const q = f.shift();
			if (q) saida.push(q);
		}
	}
	return embaralhar(saida);
}

/** Quantas questões elegíveis o banco tem para cada bloco da prova. */
export function disponiveis(banco) {
	const oficiais = (Array.isArray(banco) ? banco : []).filter(elegivel);
	return {
		fg: oficiais.filter((q) => q.parte === 'FG' && q.tipo === 'objetiva').length,
		ce: oficiais.filter((q) => q.parte === 'CE' && q.tipo === 'objetiva').length,
		discursivas: oficiais.filter((q) => q.parte === 'CE' && q.tipo === 'discursiva').length
	};
}

/** O banco tem o bastante para uma prova inteira? */
export function bancoCompleto(banco) {
	const d = disponiveis(banco);
	return d.fg >= FORMATO.fg && d.ce >= FORMATO.ce && d.discursivas >= FORMATO.discursivas;
}

/**
 * Monta uma prova nova: FG 1–15, CE 16–45 e a discursiva por último.
 * Devolve `null` se o banco não tem questões suficientes.
 */
export function montarProva(banco) {
	if (!bancoCompleto(banco)) return null;
	const oficiais = banco.filter(elegivel);
	const fg = sortearBalanceado(
		oficiais.filter((q) => q.parte === 'FG' && q.tipo === 'objetiva'),
		FORMATO.fg
	);
	const ce = sortearBalanceado(
		oficiais.filter((q) => q.parte === 'CE' && q.tipo === 'objetiva'),
		FORMATO.ce
	);
	const disc = embaralhar(
		oficiais.filter((q) => q.parte === 'CE' && q.tipo === 'discursiva')
	).slice(0, FORMATO.discursivas);
	return {
		v: 1,
		ids: [...fg, ...ce, ...disc].map((q) => q.id),
		criadaEm: Date.now(),
		gastoMs: 0,
		marcas: {},
		rascunho: '',
		i: 0,
		entregue: false,
		entregueEm: null,
		tempoEsgotado: false,
		discAuto: null
	};
}

/**
 * Confere se a lista de ids de uma prova agendada cabe no formato atual: o
 * tamanho certo e, em cada posição, o tipo que o bloco pede (FG objetiva, CE
 * objetiva, discursiva do CE). A correção é por POSIÇÃO (`blocoDe`), então
 * uma lista de outro formato seria corrigida com os blocos trocados.
 * Devolve as questões na ordem, ou `null`.
 */
export function questoesDaLista(banco, ids) {
	if (!Array.isArray(ids) || ids.length !== TOTAL_QUESTOES) return null;
	const mapa = new Map((Array.isArray(banco) ? banco : []).map((q) => [q.id, q]));
	const lista = ids.map((id) => mapa.get(id));
	const cabe = lista.every((q, k) => {
		if (!q || ehGerada(q)) return false;
		const b = blocoDe(k);
		if (b === 'DISC') return q.parte === 'CE' && q.tipo === 'discursiva';
		return q.parte === b && q.tipo === 'objetiva';
	});
	return cabe ? lista : null;
}

/**
 * Prova a partir da lista sorteada pelo professor (simulado da turma). Igual a
 * `montarProva`, mais o campo `simulado` — opcional, então provas antigas
 * (`v: 1` sem ele) continuam valendo. `null` se a lista não cabe no banco.
 */
export function montarProvaDada(banco, simulado) {
	if (!questoesDaLista(banco, simulado?.questoes)) return null;
	return {
		v: 1,
		ids: [...simulado.questoes],
		criadaEm: Date.now(),
		gastoMs: 0,
		marcas: {},
		rascunho: '',
		i: 0,
		entregue: false,
		entregueEm: null,
		tempoEsgotado: false,
		discAuto: null,
		simulado: {
			id: simulado.id,
			titulo: simulado.titulo,
			turmaId: simulado.turma?.id ?? null,
			turmaNome: simulado.turma?.nome ?? '',
			fechaEm: simulado.fecha_em
		}
	};
}

/** Bloco da questão na posição `k` (0-based) — "FG", "CE" ou "DISC". */
export function blocoDe(k) {
	if (k < FORMATO.fg) return 'FG';
	if (k < FORMATO.fg + FORMATO.ce) return 'CE';
	return 'DISC';
}

export const NOME_BLOCO = {
	FG: 'Formação Geral',
	CE: 'Componente Específico',
	DISC: 'Discursiva'
};

/**
 * Corrige a prova. `questoes` é a lista na ordem de `prova.ids`.
 *
 * As objetivas valem 45 pontos (FG + CE); a discursiva entra à parte,
 * pela autoavaliação contra o padrão do INEP — o site não tem como dar
 * nota a texto, e inventar uma ponderação que a Portaria não publica
 * seria dar ao aluno um número que parece oficial e não é.
 */
export function corrigir(prova, questoes) {
	const itens = questoes.map((q, k) => {
		const marca = prova.marcas?.[k] ?? null;
		let status;
		if (q.tipo === 'discursiva') status = prova.discAuto || 'pendente';
		// anulada não entra no sorteio, mas uma prova salva antes da anulação
		// (2019-FG-Q01 estava com gabarito "A") ainda pode trazê-la: ponto
		// para todos, como faz o INEP
		else if (q.gabarito === 'ANULADA') status = 'certa';
		else if (!marca) status = 'branco';
		else status = marca === q.gabarito ? 'certa' : 'errada';
		return { k, id: q.id, bloco: blocoDe(k), materia: q.materia || null, marca, gabarito: q.gabarito ?? null, status };
	});
	const parte = (b) => {
		const lista = itens.filter((it) => it.bloco === b);
		return {
			total: lista.length,
			certas: lista.filter((it) => it.status === 'certa').length,
			brancos: lista.filter((it) => it.status === 'branco').length
		};
	};
	const fg = parte('FG');
	const ce = parte('CE');
	const objetivas = {
		total: fg.total + ce.total,
		certas: fg.certas + ce.certas,
		brancos: fg.brancos + ce.brancos
	};

	const mapa = new Map();
	for (const it of itens) {
		if (it.bloco === 'DISC' || !it.materia) continue;
		if (!mapa.has(it.materia)) mapa.set(it.materia, { materia: it.materia, total: 0, certas: 0 });
		const m = mapa.get(it.materia);
		m.total++;
		if (it.status === 'certa') m.certas++;
	}
	// pior desempenho primeiro: é por onde o estudo deve começar
	const porMateria = [...mapa.values()].sort(
		(a, b) => a.certas / a.total - b.certas / b.total || b.total - a.total
	);

	return { itens, fg, ce, objetivas, disc: prova.discAuto || 'pendente', porMateria };
}

function ler(chave) {
	try {
		const v = localStorage.getItem(chave);
		return v ? JSON.parse(v) : null;
	} catch {
		return null;
	}
}

function gravar(chave, valor) {
	try {
		localStorage.setItem(chave, JSON.stringify(valor));
		return true;
	} catch {
		return false;
	}
}

/** Prova em andamento ou a última entregue (para rever a correção). */
export function lerProva() {
	const p = ler(CHAVE);
	if (!p || p.v !== 1 || !Array.isArray(p.ids) || !p.ids.length) return null;
	return p;
}

export function gravarProva(p) {
	return gravar(CHAVE, p);
}

export function limparProva() {
	try {
		localStorage.removeItem(CHAVE);
	} catch {
		// armazenamento bloqueado — nada a limpar
	}
}

/** Resumo do último simulado entregue, para a tela inicial do modo. */
export function lerUltimo() {
	return ler(CHAVE_ULTIMO);
}

export function gravarUltimo(r) {
	return gravar(CHAVE_ULTIMO, r);
}

/** 4h03min → "4:03:00"; usado no relógio e no tempo gasto. */
export function relogio(ms) {
	const s = Math.max(0, Math.round(ms / 1000));
	const h = Math.floor(s / 3600);
	const m = Math.floor((s % 3600) / 60);
	const ss = s % 60;
	return `${h}:${String(m).padStart(2, '0')}:${String(ss).padStart(2, '0')}`;
}

/** Simulados da turma entregues neste aparelho: `{[id]: {em, certas, total}}`. */
export function lerFeitosDaTurma() {
	const v = ler(CHAVE_TURMA);
	return v && typeof v === 'object' && !Array.isArray(v) ? v : {};
}

/** Marca um simulado da turma como entregue (guarda só o placar). */
export function marcarFeitoDaTurma(id, resumo) {
	if (!id) return false;
	const feitos = lerFeitosDaTurma();
	feitos[id] = { em: resumo.em, certas: resumo.certas, total: resumo.total };
	return gravar(CHAVE_TURMA, feitos);
}
