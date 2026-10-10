<script>
	import { onMount } from 'svelte';
	import { REDUCED } from './motion.js';

	let { valor = 0, duracao = 900 } = $props();
	let atual = $state(0);

	onMount(() => {
		if (REDUCED) {
			atual = valor;
			return;
		}
		let raf;
		const t0 = performance.now();
		const passo = (t) => {
			const p = Math.min(1, (t - t0) / duracao);
			atual = Math.round(valor * (1 - Math.pow(1 - p, 3)));
			if (p < 1) raf = requestAnimationFrame(passo);
		};
		raf = requestAnimationFrame(passo);
		return () => cancelAnimationFrame(raf);
	});
</script>

<span class="nums">{atual}</span>
