import { browser } from '$app/environment';

/** Duração padrão das transições JS. Zera com prefers-reduced-motion. */
export const REDUCED =
	browser &&
	typeof matchMedia === 'function' &&
	matchMedia('(prefers-reduced-motion: reduce)').matches;

export const DUR = REDUCED ? 0 : 240;

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
