<script>
	import { onMount } from 'svelte';
	import { Warning, X } from 'phosphor-svelte';

	// "To de olho" no DevTools.
	//
	// Isto NÃO é proteção. Qualquer pessoa que saiba usar o console desliga
	// isso em uma linha — e o gabarito está no JSON que o site inteiro
	// baixa, então quem quiser ver, vê. O que este componente faz é dizer na
	// cara que dá para ver, e dizer que ver não faz diferença.
	//
	// A forma é a mais barata que existe e a que menos atrapalha o estudo:
	// comparamos `outerWidth - innerWidth`. O DevTools encostado na lateral
	// deixa essa diferença grande; docked numa janela separada, não deixa, e
	// aí nada aparece — é o limite honesto de uma detecção que roda no
	// cliente. O atalho (F12, Ctrl+Shift+I) cobre o caso de abrir e fechar
	// rápido demais para o polling ver.
	//
	// Por que detectar mesmo assim: o objetivo é transparência. Quem estuda
	// achando que não dá para consultar o gabarito fica com uma informação a
	// menos — e o gabarito de uma questão que você errou é exatamente o dado
	// que muda o seu comportamento depois.

	let visivel = $state(false);
	let dismissed = $state(false);

	function mostrar() {
		if (!dismissed) visivel = true;
	}

	onMount(() => {
		const checaLargura = () => {
			// ~160px: a largura mínima do painel de elementos do DevTools.
			if (window.outerWidth - window.innerWidth > 160) mostrar();
		};

		const aoTeclar = (e) => {
			if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && e.key === 'I')) {
				mostrar();
			}
		};

		checaLargura();
		document.addEventListener('keydown', aoTeclar, { capture: true });
		window.addEventListener('resize', checaLargura, { passive: true });
		const timer = setInterval(checaLargura, 1500);

		return () => {
			document.removeEventListener('keydown', aoTeclar, { capture: true });
			window.removeEventListener('resize', checaLargura);
			clearInterval(timer);
		};
	});

	function fechar() {
		dismissed = true;
		visivel = false;
	}
</script>

{#if visivel}
	<!--
		role="status" + aria-live="polite": é um aviso que chega por conta
		própria, então um leitor de tela anuncia sem interromper. Fechar é
		botão de verdade (não só clique fora) porque o aviso some sozinho não
		pode — se ele some, o aluno que não viu continua sem a informação.
	-->
	<div
		class="fixed inset-x-3 bottom-3 z-50 mx-auto max-w-lg sm:bottom-5"
		role="status"
		aria-live="polite"
	>
		<div class="flex items-start gap-3 rounded-2xl border-2 border-accent/40 bg-card p-4 shadow-lg shadow-ink/10">
			<span class="mt-0.5 shrink-0 text-accent-ink" aria-hidden="true">
				<Warning size={22} weight="fill" />
			</span>
			<div class="min-w-0 flex-1">
				<p class="font-display text-sm font-extrabold tracking-tight">De olho aberto</p>
				<p class="mt-1 text-sm leading-relaxed text-pretty text-ink-soft">
					O DevTools está aberto. O gabarito está no arquivo que esta página
					baixa, então dá para ver — e dá mesmo assim.
				</p>
				<p class="mt-2 text-xs leading-relaxed text-pretty text-ink-soft">
					A ideia aqui não é esconder: é que a consulta ao gabarito antes de
					tentar não muda nada na prova. Errou a questão, volta nela depois
					que é o que treina.
				</p>
			</div>
			<button
				type="button"
				onclick={fechar}
				aria-label="Dispensar aviso"
				class="-m-1 shrink-0 rounded-lg p-2 text-ink-soft transition-colors hover:bg-bar/5 active:scale-95"
			>
				<X size={18} weight="bold" aria-hidden="true" />
			</button>
		</div>
	</div>
{/if}
