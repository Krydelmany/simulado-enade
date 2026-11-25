<script>
	import { animar, mola } from './motion.js';

	/**
	 * Selo de 3+ acertos seguidos (Treino e Estudo). Fica pendurado na borda da
	 * gaveta de feedback, fora do fluxo: não empurra o texto nem cobre o
	 * enunciado, e vai embora com a questão.
	 */
	let { n } = $props();

	let degraus = $derived(Array.from({ length: Math.min(5, n) }, (_, k) => k));

	function chegar(el) {
		animar(
			el,
			{ opacity: [0, 1], transform: ['translateY(10px) scale(0.5) rotate(-7deg)', 'translateY(0px) scale(1) rotate(0deg)'] },
			{ ...mola(300, 15), atraso: 120 }
		);
		el.querySelectorAll('rect').forEach((r, k) =>
			animar(
				r,
				{ opacity: [0, 1], transform: ['scaleY(0)', 'scaleY(1)'] },
				{ ...mola(340, 14), atraso: 220 + k * 55 }
			)
		);
	}
</script>

<span
	{@attach chegar}
	class="nums pointer-events-none absolute -top-3.5 right-3 inline-flex h-7 items-center gap-1.5 rounded-lg border border-milestone-border bg-card px-2.5 text-xs font-extrabold text-milestone-ink"
>
	<svg width={degraus.length * 5} height="14" fill="var(--milestone)" aria-hidden="true">
		{#each degraus as k (k)}
			<rect class="degrau" x={k * 5} y={10 - k * 2.5} width="4" height={4 + k * 2.5} />
		{/each}
	</svg>
	{n} seguidas
</span>

<style>
	.degrau {
		transform-box: fill-box;
		transform-origin: bottom;
	}
</style>
