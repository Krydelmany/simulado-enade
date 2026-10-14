import { reduzirMovimento } from './motion.js';

/**
 * Gestos de toque das telas de questão: deslizar a questão para os lados,
 * puxar a barra de ação para cima e arrastar o cartão-resposta para baixo.
 *
 * Tudo aqui é fábrica de attachment (`{@attach}` do Svelte 5) e só toca
 * `window` dentro dela: o módulo é importado no SSR do build.
 *
 * Regras que valem para todos (ver "Gestos e o voltar do sistema" no AGENTS.md):
 *  - só TOQUE: mouse e caneta no desktop ficam de fora;
 *  - listeners PASSIVOS e `touch-action` intacto na área de leitura — a pinça
 *    (zoom de acessibilidade) continua funcionando em todo lugar;
 *  - o gesto nunca responde, pula nem encerra: só faz o que um botão
 *    visível ao lado já faz;
 *  - depois de um arraste, o clique que o navegador sintetiza no touchend é
 *    engolido — sem isso, soltar o dedo em cima de uma alternativa a marcava.
 */

/** Faixa de cada lateral reservada ao voltar do sistema (px). */
export const BORDA_PX = 24;
// faixa de baixo reservada ao gesto de início do iOS/Android
const BASE_PX = 24;
// movimento mínimo antes de decidir o eixo
const FOLGA_PX = 10;
// o eixo principal precisa ser 1,5× o outro; senão é rolagem diagonal e abandona
const RAZAO_EIXO = 1.5;
// parado mais que isso sem decidir = o aluno está selecionando texto
const TOQUE_LONGO_MS = 450;
const DISPARO_MIN_PX = 64;
const DISPARO_FRACAO = 0.2;
// peteleco: velocidade nos últimos 100 ms e um mínimo de deslocamento
const RAPIDO_PX_MS = 0.4;
const RAPIDO_MIN_PX = 32;
// quanto o cartão cede quando aquela direção está bloqueada
const ELASTICO_PX = 32;
const PUXAR_PX = 40;
const FECHAR_PX = 80;
const BLOQUEIO_CLIQUE_MS = 400;

/** Evento disparado em `window` a cada troca de questão por gesto (dispensa a dica). */
export const EVENTO_DESLIZE = 'enade-deslize';

let bloquearAte = 0;
let engolindo = false;

function engolir(e) {
	if (performance.now() < bloquearAte) {
		e.preventDefault();
		e.stopPropagation();
	}
}

/** Engole, em captura, os cliques dos próximos 400 ms (o clique fantasma do arraste). */
export function suprimirClique() {
	bloquearAte = performance.now() + BLOQUEIO_CLIQUE_MS;
	if (!engolindo) {
		engolindo = true;
		window.addEventListener('click', engolir, true);
	}
}

function toqueLivre(e) {
	const alvo = e.target instanceof Element ? e.target : null;
	if (alvo?.closest('input, textarea, select, [contenteditable], [data-sem-gesto]')) return false;
	const sel = window.getSelection?.();
	if (sel && !sel.isCollapsed) return false;
	// pinça ativa: o dedo está passeando pela página ampliada, não deslizando
	if ((window.visualViewport?.scale ?? 1) > 1.01) return false;
	return true;
}

function haModal() {
	return !!document.querySelector('[aria-modal="true"]');
}

function voltarAoLugar(no) {
	if (!no.style.transform) return;
	no.style.transition = 'transform 180ms ease-out';
	no.style.transform = '';
	setTimeout(() => {
		if (!no.style.transform) no.style.transition = '';
	}, 220);
}

/**
 * Núcleo: acompanha UM dedo, decide o eixo e só então assume o gesto.
 * Devolve a função que desliga os listeners.
 */
function rastrear(no, { eixo, comecar, mover, soltar, cancelar }) {
	let ativo = false;
	let decidido = false;
	let x0 = 0;
	let y0 = 0;
	let t0 = 0;
	let dx = 0;
	let dy = 0;
	let amostras = [];

	function abandonar() {
		ativo = false;
		decidido = false;
	}

	function inicio(e) {
		// segundo dedo no meio de um gesto já decidido (a pinça): devolve o
		// cartão ao lugar antes de largar — sem isso ele ficava preso no
		// translateX, cortado na borda e com o zoom da figura fora do lugar
		if (ativo && decidido) cancelar();
		abandonar();
		if (e.touches.length !== 1 || !toqueLivre(e)) return;
		const t = e.touches[0];
		if (comecar(t, e) === false) return;
		ativo = true;
		x0 = t.clientX;
		y0 = t.clientY;
		t0 = performance.now();
		dx = 0;
		dy = 0;
		amostras = [{ t: t0, x: x0, y: y0 }];
	}

	function movimento(e) {
		if (!ativo) return;
		if (e.touches.length > 1) {
			if (decidido) cancelar();
			abandonar();
			return;
		}
		const t = e.touches[0];
		const mx = t.clientX - x0;
		const my = t.clientY - y0;
		const agora = performance.now();
		if (!decidido) {
			const principal = Math.abs(eixo === 'x' ? mx : my);
			const outro = Math.abs(eixo === 'x' ? my : mx);
			if (Math.max(principal, outro) < FOLGA_PX) {
				if (agora - t0 > TOQUE_LONGO_MS) abandonar();
				return;
			}
			if (principal < RAZAO_EIXO * outro) {
				abandonar();
				return;
			}
			decidido = true;
			suprimirClique();
		}
		dx = mx;
		dy = my;
		amostras.push({ t: agora, x: t.clientX, y: t.clientY });
		while (amostras.length > 2 && agora - amostras[0].t > 100) amostras.shift();
		mover({ dx, dy });
	}

	function fim(e) {
		if (!ativo) return;
		const era = decidido;
		abandonar();
		if (!era) return;
		if (e.cancelable) e.preventDefault();
		suprimirClique();
		const a = amostras[0];
		const b = amostras[amostras.length - 1];
		const dt = Math.max(1, b.t - a.t);
		soltar({ dx, dy, vx: (b.x - a.x) / dt, vy: (b.y - a.y) / dt });
	}

	// o sistema tomou o toque (voltar por gesto do Android, rolagem nativa)
	function cancelado() {
		if (ativo && decidido) cancelar();
		abandonar();
	}

	no.addEventListener('touchstart', inicio, { passive: true });
	no.addEventListener('touchmove', movimento, { passive: true });
	no.addEventListener('touchend', fim, { passive: false });
	no.addEventListener('touchcancel', cancelado, { passive: true });
	return () => {
		no.removeEventListener('touchstart', inicio);
		no.removeEventListener('touchmove', movimento);
		no.removeEventListener('touchend', fim);
		no.removeEventListener('touchcancel', cancelado);
	};
}

function passouDoPonto(d, v, limiar) {
	return Math.abs(d) >= limiar || (Math.abs(v) >= RAPIDO_PX_MS && Math.abs(d) >= RAPIDO_MIN_PX && Math.sign(v) === Math.sign(d));
}

/**
 * Deslizar a questão para os lados: para a esquerda vai à próxima, para a
 * direita volta. A direção bloqueada só cede um pouco (efeito elástico).
 *
 * `estado` é uma FUNÇÃO lida a cada gesto, nunca no attach: assim o
 * attachment não se refaz a cada resposta.
 *
 * NUNCA deixa `transform`/`will-change` no nó: o zoom da figura é
 * `position: fixed` lá dentro, e um transform viraria o bloco de contenção.
 *
 * @param {() => { anterior: boolean, proxima: boolean, onAnterior: () => void, onProxima: () => void }} estado
 */
export function deslizarQuestoes(estado) {
	return (no) => {
		let largura = 0;
		const desligar = rastrear(no, {
			eixo: 'x',
			comecar(t) {
				if (haModal()) return false;
				largura = window.innerWidth;
				// as bordas são do voltar do sistema
				if (t.clientX < BORDA_PX || t.clientX > largura - BORDA_PX) return false;
			},
			mover({ dx }) {
				if (reduzirMovimento()) return;
				const e = estado();
				const pode = dx < 0 ? e.proxima : e.anterior;
				const x = pode ? dx * 0.85 : Math.sign(dx) * Math.min(ELASTICO_PX, Math.abs(dx) * 0.25);
				no.style.transition = 'none';
				no.style.transform = `translateX(${x}px)`;
			},
			soltar({ dx, vx }) {
				const e = estado();
				const lado = dx < 0 ? 'proxima' : 'anterior';
				const limiar = Math.max(DISPARO_MIN_PX, largura * DISPARO_FRACAO);
				if (passouDoPonto(dx, vx, limiar) && e[lado]) {
					// a questão nova entra pelo `in:fly` da página; o cartão
					// velho sai sem animação de volta
					no.style.transition = '';
					no.style.transform = '';
					window.dispatchEvent(new CustomEvent(EVENTO_DESLIZE));
					if (lado === 'proxima') e.onProxima();
					else e.onAnterior();
				} else {
					voltarAoLugar(no);
				}
			},
			cancelar() {
				voltarAoLugar(no);
			}
		});
		return () => {
			desligar();
			no.style.transition = '';
			no.style.transform = '';
		};
	};
}

/**
 * Puxar a barra de ação para cima chama `acao` (no simulado: abre o
 * cartão-resposta).
 * @param {() => void} acao
 */
export function puxarParaCima(acao) {
	return (no) => {
		// sem isso, arrastar a barra fixa rolaria a página por trás (e no
		// Safari mexeria na barra de endereço). A barra não é área de leitura.
		no.style.touchAction = 'none';
		const desligar = rastrear(no, {
			eixo: 'y',
			comecar(t) {
				if (haModal()) return false;
				const base = Math.max(BASE_PX, parseFloat(getComputedStyle(no).paddingBottom) || 0);
				// a faixa de baixo é do gesto de início do sistema
				if (t.clientY >= window.innerHeight - base) return false;
			},
			mover({ dy }) {
				if (reduzirMovimento()) return;
				no.style.transition = 'none';
				no.style.transform = dy < 0 ? `translateY(${Math.max(-24, dy * 0.4)}px)` : '';
			},
			soltar({ dy, vy }) {
				voltarAoLugar(no);
				if (dy <= -PUXAR_PX || (vy <= -RAPIDO_PX_MS && dy <= -20)) acao();
			},
			cancelar() {
				voltarAoLugar(no);
			}
		});
		return () => {
			desligar();
			no.style.touchAction = '';
			no.style.transition = '';
			no.style.transform = '';
		};
	};
}

/**
 * Arrastar um painel para baixo chama `acao` (fecha o cartão-resposta).
 * Só começa com a lista no topo: rolada, arrastar para baixo é rolar de volta.
 * @param {() => void} acao
 */
export function arrastarParaFechar(acao) {
	return (no) => {
		const desligar = rastrear(no, {
			eixo: 'y',
			comecar() {
				if (no.scrollTop > 0) return false;
			},
			mover({ dy }) {
				no.style.transition = 'none';
				no.style.transform = dy > 0 && !reduzirMovimento() ? `translateY(${dy}px)` : '';
			},
			soltar({ dy, vy }) {
				if (dy >= FECHAR_PX || (vy >= RAPIDO_PX_MS && dy >= RAPIDO_MIN_PX)) acao();
				else voltarAoLugar(no);
			},
			cancelar() {
				voltarAoLugar(no);
			}
		});
		return () => {
			desligar();
			no.style.transition = '';
			no.style.transform = '';
		};
	};
}
