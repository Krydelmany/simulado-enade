import { browser } from '$app/environment';

/** Duração padrão das transições JS. Zera com prefers-reduced-motion. */
export const REDUCED =
	browser &&
	typeof matchMedia === 'function' &&
	matchMedia('(prefers-reduced-motion: reduce)').matches;

export const DUR = REDUCED ? 0 : 240;
