<script>
	import { puxarParaCima } from './gestos.js';

	/**
	 * Barra fixa de ação no rodapé.
	 *
	 * Ela NÃO empurra o conteúdo (position: fixed), então:
	 *  - respeita a área segura do iOS no fundo (`env(safe-area-inset-bottom)`);
	 *  - as telas de quiz reservam padding-bottom equivalente (ver `+layout.svelte`)
	 *    para a última alternativa nunca ficar escondida atrás dela;
	 *  - `desabilitado` + `aviso` travam o CTA até o aluno responder, dizendo o que fazer.
	 * Aceita conteúdo (snippet default `children`) para a faixa de navegação acima do CTA.
	 * Com `onPuxar`, puxar a barra para cima (toque) chama a função — no simulado,
	 * abre o cartão-resposta — e uma alça aparece no topo no celular. Passe uma
	 * função ESTÁVEL: trocar a referência refaz o attachment.
	 */
	let {
		rotulo,
		onClick,
		mostrarXP = false,
		xpValor = 10,
		desabilitado = false,
		aviso = '',
		onPuxar = null,
		children
	} = $props();

	// id estável por instância para ligar o botão ao texto de orientação (a11y)
	const idAviso = $props.id();
</script>

<div
	data-barra-acao
	class="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-paper"
	style="padding-bottom: env(safe-area-inset-bottom);"
	{@attach onPuxar && puxarParaCima(onPuxar)}
>
	<div class="mx-auto max-w-3xl px-4 pt-2 pb-3">
		{#if onPuxar}
			<span aria-hidden="true" class="mx-auto mb-1.5 block h-1 w-9 rounded-full bg-line sm:hidden"></span>
		{/if}
		{#if children}
			<div class="mb-2">{@render children()}</div>
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
				<p id={idAviso} class="mb-1.5 text-center text-xs font-semibold text-ink-soft" role="status">
					{aviso}
				</p>
			{/if}
			<button
				type="button"
				onclick={onClick}
				disabled={desabilitado}
				aria-describedby={desabilitado && aviso ? idAviso : undefined}
				class="min-h-[52px] w-full rounded-[14px] font-display text-lg font-bold {desabilitado
					? 'cursor-not-allowed bg-tile text-ink-soft'
					: 'btn3d duo-accent'}"
			>
				{rotulo}
			</button>
		</div>
	</div>
</div>
