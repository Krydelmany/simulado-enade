<script>
	import { ArrowRight } from 'phosphor-svelte';
	import { puxarParaCima } from './gestos.js';

	/**
	 * Barra de ação INLINE, no fim da questão (usada no Simulado).
	 *
	 * Antes era `position: fixed` no rodapé: no celular ela cobria a última
	 * alternativa e obrigava o layout a reservar `pb-32`; no desktop ficava
	 * longe do conteúdo. Agora é um cartão no fluxo.
	 *
	 * `onAnterior` é opcional: sem ele, o CTA ocupa a linha inteira (o
	 * simulado usa os próprios controles no bloco de children).
	 * Com `onPuxar`, puxar o cartão para cima (toque) chama a função — no
	 * simulado, abre o cartão-resposta. Passe uma função ESTÁVEL.
	 */
	let {
		rotulo,
		onClick,
		mostrarXP = false,
		xpValor = 10,
		desabilitado = false,
		aviso = '',
		onAnterior = null,
		anteriorDesabilitado = false,
		onPuxar = null,
		children
	} = $props();

	// id estável por instância para ligar o botão ao texto de orientação (a11y)
	const idAviso = $props.id();
</script>

<div
	data-barra-acao
	class="superficie mt-4 rounded-3xl p-4 sm:p-5"
	{@attach onPuxar && puxarParaCima(onPuxar)}
>
	{#if onPuxar}
		<span aria-hidden="true" class="mx-auto mb-2.5 block h-1 w-9 rounded-full bg-line sm:hidden"></span>
	{/if}
	{#if children}
		<div class="mb-3">{@render children()}</div>
	{/if}
	<div class="relative">
		{#if mostrarXP}
			<span
				class="xp-float nums pointer-events-none absolute -top-11 right-2 rounded-full border border-milestone-border bg-milestone-soft px-3 py-1 text-xs font-extrabold text-milestone-ink shadow-sm"
				role="status"
			>
				+{xpValor} XP
			</span>
		{/if}
		{#if desabilitado && aviso}
			<p id={idAviso} class="mb-2.5 text-center text-xs font-medium text-ink-soft" role="status">
				{aviso}
			</p>
		{/if}
		<div class={onAnterior ? 'flex flex-col gap-2 sm:flex-row' : ''}>
			{#if onAnterior}
				<button
					type="button"
					onclick={onAnterior}
					disabled={anteriorDesabilitado}
					class="btn-suave min-h-12 rounded-full px-5 font-display text-sm font-bold disabled:pointer-events-none disabled:opacity-40"
				>
					Anterior
				</button>
			{/if}
			<button
				type="button"
				onclick={onClick}
				disabled={desabilitado}
				aria-describedby={desabilitado && aviso ? idAviso : undefined}
				class="flex min-h-12 items-center justify-center gap-2 rounded-full px-6 font-display text-base font-bold {onAnterior
					? 'flex-1'
					: 'w-full'} {desabilitado
					? 'cursor-not-allowed border border-line bg-panel text-ink-soft'
					: 'btn-primario'}"
			>
				<span>{rotulo}</span>
				{#if !desabilitado}
					<ArrowRight size={17} weight="bold" aria-hidden="true" />
				{/if}
			</button>
		</div>
	</div>
</div>
