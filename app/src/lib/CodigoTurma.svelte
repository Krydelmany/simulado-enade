<script>
	// Código da turma em quadradinhos, como o código de verificação do banco.
	// É UM input só, transparente por cima das caixas: colar (até o link
	// inteiro do convite), apagar e o teclado do celular funcionam como num
	// campo normal. Um input por caixa quebra o colar e o leitor de tela lê
	// seis campos sem nome.
	import { limparCodigo, TAMANHO_CODIGO } from './nuvem.js';

	let { valor = $bindable(''), id = 'codigo', descricao = '' } = $props();

	const CAIXAS = Array.from({ length: TAMANHO_CODIGO }, (_, i) => i);

	let focado = $state(false);
	let ativa = $derived(Math.min(valor.length, TAMANHO_CODIGO - 1));

	function aoDigitar(ev) {
		valor = limparCodigo(ev.currentTarget.value);
		// o que não é código (espaço, símbolo, o resto do link) some do campo também
		ev.currentTarget.value = valor;
	}

	// o cursor fica sempre no fim: tocar numa caixa do meio e digitar
	// inseriria ali e empurraria o resto
	function cursorNoFim(ev) {
		const el = ev.currentTarget;
		requestAnimationFrame(() => el.setSelectionRange(el.value.length, el.value.length));
	}
</script>

<div class="relative">
	<input
		{id}
		value={valor}
		oninput={aoDigitar}
		onfocus={(ev) => {
			focado = true;
			cursorNoFim(ev);
		}}
		onblur={() => (focado = false)}
		onclick={cursorNoFim}
		required
		pattern={`[A-Za-z0-9]{${TAMANHO_CODIGO}}`}
		title="O código tem {TAMANHO_CODIGO} letras e números"
		autocomplete="off"
		autocapitalize="characters"
		autocorrect="off"
		spellcheck="false"
		aria-describedby={descricao || undefined}
		class="codigo-real absolute inset-0 z-10 h-full w-full bg-transparent text-base"
	/>
	<div class="grid grid-cols-6 gap-1.5 sm:gap-2" aria-hidden="true">
		{#each CAIXAS as i (i)}
			<div
				class="relative flex h-14 items-center justify-center rounded-xl border-2 bg-paper font-display text-2xl font-extrabold sm:h-16 sm:text-3xl {focado &&
				i === ativa
					? 'border-accent'
					: valor[i]
						? 'border-ink-soft'
						: 'border-line'}"
			>
				{valor[i] ?? ''}
				{#if focado && i === valor.length}
					<span class="cursor-piscando absolute h-7 w-0.5 rounded-full bg-accent"></span>
				{/if}
			</div>
		{/each}
	</div>
</div>

<style>
	/* o texto e o cursor do input de verdade ficam invisíveis: quem mostra é a caixa */
	.codigo-real {
		color: transparent;
		caret-color: transparent;
		border: 0;
		outline: none;
		letter-spacing: 1em;
	}
	.codigo-real::selection {
		background: transparent;
	}
	.cursor-piscando {
		animation: piscar 1s steps(1) infinite;
	}
	@keyframes piscar {
		50% {
			opacity: 0;
		}
	}
</style>
