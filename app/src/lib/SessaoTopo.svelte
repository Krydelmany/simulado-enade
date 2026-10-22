<script>
	import { Lightning, X } from 'phosphor-svelte';

	let { titulo, detalhe = '', progresso = 0, xp = 0, aoFechar } = $props();

	// posição real da sessão em % — substitui a etiqueta decorativa fixa
	// ("SIM-ENADE // REV A"), que só ocupava espaço e era igual em toda sessão.
	let pct = $derived(Math.round(progresso * 100));
</script>

<div class="blueprint faixa px-4 pt-4 pb-5 text-white">
	<div class="relative mx-auto max-w-3xl">
		<div class="flex items-center gap-3">
			<button
				type="button"
				onclick={aoFechar}
				aria-label="Encerrar sessão"
				class="flex h-11 min-w-11 items-center justify-center rounded-full bg-white/10 transition-transform active:scale-95"
			>
				<X size={22} weight="bold" aria-hidden="true" />
			</button>
			<span class="flex-1"></span>
			<p class="nums flex items-center gap-1.5 rounded-full bg-accent-soft px-3.5 py-1.5 text-sm font-extrabold text-accent-ink">
				<Lightning size={16} weight="fill" aria-hidden="true" />
				{xp} XP
			</p>
		</div>
		<div class="mt-3 flex items-baseline justify-between gap-3">
			<p class="font-display text-[17px] font-bold">{titulo}</p>
			<div class="shrink-0 text-right">
				{#if detalhe}
					<p class="text-sm font-medium text-bar-fg">{detalhe}</p>
				{/if}
				<p class="nums text-label font-semibold text-white/65">{pct}% concluído</p>
			</div>
		</div>
		<div
			class="mt-2 h-2.5 overflow-hidden rounded-full bg-white/15"
			role="progressbar"
			aria-label="Progresso da sessão"
			aria-valuemin="0"
			aria-valuemax="100"
			aria-valuenow={pct}
		>
			<div
				class="h-full rounded-full bg-accent-bar transition-[width] duration-500 ease-out"
				style="width: {pct}%"
			></div>
		</div>
	</div>
</div>
