<script>
	import { puxarParaCima } from './gestos.js';

	/**
	 * Barra de ação INLINE, no fim da questão.
	 *
	 * Antes era `position: fixed` no rodapé: no celular ela cobria a última
	 * alternativa e obrigava o layout a reservar `pb-32`; no desktop ficava
	 * longe do conteúdo. Agora é um cartão no fluxo, com a mesma dupla
	 * Anterior/Próxima do questionário POO.
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
	class="mt-4 rounded-3xl border border-line bg-card p-4 sm:p-5"
	{@attach onPuxar && puxarParaCima(onPuxar)}
>
	{#if onPuxar}
		<span aria-hidden="true" class="mx-auto mb-2 block h-1 w-9 rounded-full bg-line sm:hidden"></span>
	{/if}
	{#if children}
		<div class="mb-3">{@render children()}</div>
	{/if}
	<div class="relative">
		{#if mostrarXP}
			<span
				class="xp-float nums pointer-events-none absolute -top-11 right-3 rounded-full bg-accent-soft px-3 py-1 text-sm font-extrabold text-accent-ink shadow"
				role="status"
			>
				+{xpValor} XP
			</span>
		{/if}
		{#if desabilitado && aviso}
			<p id={idAviso} class="mb-2 text-center text-xs font-semibold text-ink-soft" role="status">
				{aviso}
			</p>
		{/if}
		<div class={onAnterior ? 'flex flex-col gap-2 sm:flex-row' : ''}>
			{#if onAnterior}
				<button
					type="button"
					onclick={onAnterior}
					disabled={anteriorDesabilitado}
					class="min-h-[52px] rounded-[14px] border-2 border-line bg-card px-5 font-display text-base font-bold transition-transform active:scale-[0.98] disabled:opacity-40"
				>
					Anterior
				</button>
			{/if}
			<button
				type="button"
				onclick={onClick}
				disabled={desabilitado}
				aria-describedby={desabilitado && aviso ? idAviso : undefined}
				class="min-h-[52px] rounded-[14px] font-display text-lg font-bold transition-transform active:scale-[0.99] {onAnterior
					? 'flex-1'
					: 'w-full'} {desabilitado ? 'cursor-not-allowed bg-tile text-ink-soft' : 'btn3d duo-accent'}"
			>
				{rotulo}
			</button>
		</div>
	</div>
</div>
