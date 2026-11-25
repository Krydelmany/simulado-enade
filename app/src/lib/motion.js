import { browser } from '$app/environment';

/** Duração padrão das transições JS (< 250 ms). Zera com prefers-reduced-motion. */
export const REDUCED =
	browser &&
	typeof matchMedia === 'function' &&
	matchMedia('(prefers-reduced-motion: reduce)').matches;

export const DUR = REDUCED ? 0 : 200;
export const DUR_RAPIDO = REDUCED ? 0 : 140;

/**
 * Checagem AO VIVO da preferência — o usuário pode mudar o ajuste do sistema
 * sem recarregar a página. `REDUCED` é lido uma vez no import (bom para o SSR);
 * use esta função quando a decisão acontece em runtime (ex.: Contador).
 */
export function reduzirMovimento() {
	return (
		!browser ||
		(typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches)
	);
}

/** Saída firme, sem estouro (mesma curva das animações do `app.css`). */
export const SAIDA = 'cubic-bezier(0.22, 1, 0.36, 1)';

/**
 * Mola física (massa 1 + rigidez + amortecimento) amostrada em `linear()`, para
 * a Web Animations API rodar a física no compositor. É o que a `motion` faz por
 * baixo; aqui cabe em 15 linhas e não custa 6 kB (gzip) por aluno.
 * @param {number} [rigidez]
 * @param {number} [amortecimento] abaixo de 2·√rigidez a mola passa do ponto e volta
 * @returns {{curva: string, duracao: number}} pronto para espalhar em `animar`
 */
export function mola(rigidez = 210, amortecimento = 17) {
	const w0 = Math.sqrt(rigidez);
	const zeta = Math.min(0.999, amortecimento / (2 * w0));
	const wd = w0 * Math.sqrt(1 - zeta * zeta);
	// acaba quando a oscilação que sobra não chega a 0,5% do caminho
	const fim = -Math.log(0.005) / (zeta * w0);
	const pontos = Array.from({ length: 33 }, (_, k) => {
		if (k === 32) return 1;
		const t = (k / 32) * fim;
		const x =
			1 - Math.exp(-zeta * w0 * t) * (Math.cos(wd * t) + ((zeta * w0) / wd) * Math.sin(wd * t));
		return Math.round(x * 1000) / 1000;
	});
	return { curva: `linear(${pontos.join(', ')})`, duracao: Math.round(fim * 1000) };
}

/**
 * Anima um elemento ATÉ o estado em que ele já está no HTML/CSS.
 *
 * O estado final mora sempre no markup, e a animação só descreve a chegada
 * (`fill: 'backwards'`, nunca `forwards`). Por isso nada fica preso em
 * `opacity: 0`, barra vazia ou traço invisível: com movimento reduzido, sem
 * suporte ou com a animação cancelada, o elemento simplesmente aparece pronto.
 *
 * @param {Element | null | undefined} el
 * @param {Keyframe[] | PropertyIndexedKeyframes} quadros o último quadro é o estado natural
 * @param {{duracao?: number, atraso?: number, curva?: string}} [opcoes]
 * @returns {Animation | null} `null` quando não há o que animar
 */
export function animar(el, quadros, { duracao = 240, atraso = 0, curva = SAIDA } = {}) {
	if (!el?.animate || reduzirMovimento()) return null;
	const opcoes = { duration: duracao, delay: atraso, easing: curva, fill: 'backwards' };
	try {
		return el.animate(quadros, opcoes);
	} catch {
		// `linear()` é de 2023: navegador mais velho recusa a mola
		return el.animate(quadros, { ...opcoes, easing: 'cubic-bezier(0.34, 1.4, 0.64, 1)' });
	}
}
