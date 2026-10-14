<script>
	import { onMount } from 'svelte';
	import { HandSwipeLeft, X } from 'phosphor-svelte';
	import { EVENTO_DESLIZE } from './gestos.js';

	/**
	 * Dica de primeira vez dos gestos, só em tela de toque. Some no X ou no
	 * primeiro deslize, e não volta: os ids já vistos ficam em
	 * `localStorage['enade-dica-gestos']` (array, sem `v`; o que não for
	 * array vale como nada visto).
	 */
	let { id, texto } = $props();

	const CHAVE = 'enade-dica-gestos';
	let visivel = $state(false);

	function lerVistas() {
		const v = JSON.parse(localStorage.getItem(CHAVE) || '[]');
		return Array.isArray(v) ? v : [];
	}

	function dispensar() {
		visivel = false;
		try {
			const vistas = lerVistas();
			if (!vistas.includes(id)) localStorage.setItem(CHAVE, JSON.stringify([...vistas, id]));
		} catch {
			// storage bloqueado ou cheio: só não lembra
		}
	}

	onMount(() => {
		if (!matchMedia('(pointer: coarse)').matches) return;
		let vistas;
		try {
			vistas = lerVistas();
		} catch {
			// com storage bloqueado a dica voltaria a cada visita: melhor não mostrar
			return;
		}
		if (vistas.includes(id)) return;
		visivel = true;
		window.addEventListener(EVENTO_DESLIZE, dispensar, { once: true });
		return () => window.removeEventListener(EVENTO_DESLIZE, dispensar);
	});
</script>

{#if visivel}
	<div
		role="status"
		class="mb-3 flex items-start gap-3 rounded-2xl border border-line bg-panel p-3 text-sm"
	>
		<HandSwipeLeft size={22} weight="bold" class="mt-0.5 shrink-0 text-accent-ink" aria-hidden="true" />
		<p class="flex-1 text-pretty">{texto}</p>
		<button
			type="button"
			onclick={dispensar}
			aria-label="Dispensar dica"
			class="-my-2 -mr-2 flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-ink-soft hover:bg-tile"
		>
			<X size={18} weight="bold" aria-hidden="true" />
		</button>
	</div>
{/if}
