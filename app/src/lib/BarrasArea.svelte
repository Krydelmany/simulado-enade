<script>
	import { onMount } from 'svelte';
	import { animar, mola } from './motion.js';

	/**
	 * Barras de desempenho por área ou matéria. Enchem com mola da esquerda para
	 * a direita quando chegam à tela: no simulado a lista fica bem abaixo da
	 * dobra, e a animação rodaria sem ninguém ver.
	 * `linhas`: `[{ id, nome, certas, total }]`.
	 */
	let { linhas = [], animado = true, atraso = 0, grossa = false } = $props();

	let raiz;

	onMount(() => {
		if (!animado || !raiz) return;
		const encher = (el, espera) =>
			animar(
				el.firstElementChild,
				{ transform: ['scaleX(0)', 'scaleX(1)'] },
				{ ...mola(150, 15), atraso: espera }
			);
		// Quem já está na tela anima JÁ, no mesmo quadro da montagem: o observador
		// só avisa um quadro depois, e a barra piscava cheia antes de zerar.
		const fora = [];
		let k = 0;
		for (const el of raiz.querySelectorAll('[data-barra]')) {
			if (el.getBoundingClientRect().top < window.innerHeight) encher(el, atraso + k++ * 60);
			else fora.push(el);
		}
		if (!fora.length || typeof IntersectionObserver !== 'function') return;
		const obs = new IntersectionObserver(
			(entradas) => {
				entradas
					.filter((e) => e.isIntersecting)
					.forEach((e, j) => {
						obs.unobserve(e.target);
						encher(e.target, j * 60);
					});
			},
			// um pouco antes da borda, pelo mesmo motivo
			{ rootMargin: '0px 0px 48px 0px' }
		);
		for (const el of fora) obs.observe(el);
		return () => obs.disconnect();
	});
</script>

<div bind:this={raiz} class="space-y-3">
	{#each linhas as l (l.id)}
		<div>
			<div class="flex items-baseline justify-between gap-3 text-sm">
				<p class="truncate font-semibold text-ink">{l.nome}</p>
				<p class="nums shrink-0 font-bold text-ink">{l.certas}/{l.total}</p>
			</div>
			<div data-barra class="mt-1.5 overflow-hidden rounded-full bg-track {grossa ? 'h-3' : 'h-2'}">
				<div
					class="h-full origin-left rounded-full bg-accent-bar"
					style="width: {l.total ? (l.certas / l.total) * 100 : 0}%"
				></div>
			</div>
		</div>
	{/each}
</div>
