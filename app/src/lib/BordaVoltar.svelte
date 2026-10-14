<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { CaretLeft, CaretRight } from 'phosphor-svelte';
	import { BORDA_PX, suprimirClique } from './gestos.js';
	import { temCamadas } from './camadas.svelte.js';

	/**
	 * Voltar puxando da borda da tela para o meio — RESERVA para aparelho
	 * sem esse gesto no sistema (Android com 3 botões, tela de toque no
	 * computador). Onde o sistema tem o gesto, ele ganha:
	 *  - no iOS a borda ESQUERDA é do Safari, então aqui ela fica de fora
	 *    (seriam dois voltares de uma vez);
	 *  - no Android com gestos o sistema cancela o toque (touchcancel) e
	 *    isto nunca dispara.
	 * Só age no touchend. O voltar fecha a camada de cima da rota (ver
	 * `camadas.svelte.js`) ou, na base, leva à home.
	 */
	let { ativo = false } = $props();

	const LIMIAR = 64;

	let lado = $state(null); // 'esq' | 'dir' enquanto o gesto está decidido
	let y = $state(0);
	let puxado = $state(0);
	let altura = $state(800);

	function voltar() {
		// na base da rota NÃO usa history.back(): quem chegou por link
		// direto sairia do site. A tela anterior é a home, como o X do treino
		// — sem confirmação, porque tudo já foi gravado.
		if (temCamadas()) history.back();
		else goto('/');
	}

	onMount(() => {
		const ios =
			/iP(hone|ad|od)/.test(navigator.userAgent) ||
			(navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
		let candidato = null;
		let decidido = false;
		let x0 = 0;
		let y0 = 0;

		function zerar() {
			candidato = null;
			decidido = false;
			lado = null;
			puxado = 0;
		}

		function inicio(e) {
			zerar();
			if (!ativo || e.touches.length !== 1) return;
			const t = e.touches[0];
			if (e.target instanceof Element && e.target.closest('input, textarea, select')) return;
			if (t.clientX <= BORDA_PX && !ios) candidato = 'esq';
			else if (t.clientX >= window.innerWidth - BORDA_PX) candidato = 'dir';
			else return;
			x0 = t.clientX;
			y0 = t.clientY;
			altura = window.innerHeight;
		}

		function movimento(e) {
			if (!candidato) return;
			if (e.touches.length > 1) return zerar();
			const t = e.touches[0];
			const dentro = (candidato === 'esq' ? 1 : -1) * (t.clientX - x0);
			const dy = t.clientY - y0;
			if (!decidido) {
				if (Math.max(Math.abs(dentro), Math.abs(dy)) < 10) return;
				if (dentro < 1.2 * Math.abs(dy)) return zerar();
				decidido = true;
				suprimirClique();
				lado = candidato;
			}
			y = t.clientY;
			puxado = Math.max(0, dentro);
		}

		function fim(e) {
			if (!decidido) return zerar();
			if (e.cancelable) e.preventDefault();
			suprimirClique();
			const vai = puxado >= LIMIAR;
			zerar();
			if (vai) voltar();
		}

		window.addEventListener('touchstart', inicio, { passive: true });
		window.addEventListener('touchmove', movimento, { passive: true });
		window.addEventListener('touchend', fim, { passive: false });
		window.addEventListener('touchcancel', zerar, { passive: true });
		return () => {
			window.removeEventListener('touchstart', inicio);
			window.removeEventListener('touchmove', movimento);
			window.removeEventListener('touchend', fim);
			window.removeEventListener('touchcancel', zerar);
		};
	});

	const sentido = $derived(lado === 'dir' ? -1 : 1);
	const armado = $derived(puxado >= LIMIAR);
</script>

{#if lado}
	<div
		aria-hidden="true"
		class="pointer-events-none fixed z-60 flex h-11 w-11 items-center justify-center rounded-full border shadow-md {armado
			? 'border-accent bg-accent text-white'
			: 'border-line bg-card text-ink'} {lado === 'esq' ? 'left-0' : 'right-0'}"
		style="top: {Math.min(Math.max(y - 22, 8), altura - 52)}px; transform: translateX({sentido *
			(Math.min(puxado, 88) * 0.75 - 44)}px); opacity: {Math.min(1, puxado / 32)};"
	>
		{#if lado === 'esq'}
			<CaretLeft size={22} weight="bold" />
		{:else}
			<CaretRight size={22} weight="bold" />
		{/if}
	</div>
{/if}
