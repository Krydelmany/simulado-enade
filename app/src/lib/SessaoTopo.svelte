<script>
	import { Lightning, X } from 'phosphor-svelte';

	let { titulo, detalhe = '', progresso = 0, xp = 0, aoFechar } = $props();

	let pct = $derived(Math.min(100, Math.max(0, Math.round(progresso * 100))));
</script>

<div class="superficie rounded-3xl px-4 py-3.5 sm:px-5 sm:py-4">
	<div class="flex items-center gap-3">
		<button
			type="button"
			onclick={aoFechar}
			aria-label="Encerrar sessão"
			class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-line bg-paper text-ink-soft transition-colors hover:border-line-strong hover:text-ink active:scale-95"
		>
			<X size={19} weight="bold" aria-hidden="true" />
		</button>

		<div class="min-w-0 flex-1">
			<div class="flex items-baseline justify-between gap-2">
				<p class="truncate font-display text-sm font-bold text-ink sm:text-[15px]">{titulo}</p>
				<p class="nums shrink-0 text-xs font-semibold text-ink-soft">
					{#if detalhe}{detalhe} · {/if}{pct}%
				</p>
			</div>
			<div
				class="mt-2 h-2.5 overflow-hidden rounded-full bg-track"
				role="progressbar"
				aria-label="Progresso da sessão"
				aria-valuemin="0"
				aria-valuemax="100"
				aria-valuenow={pct}
			>
				<div
					class="h-full rounded-full transition-[width,background-color] duration-300 ease-out {pct >= 100
						? 'bg-ok-solid'
						: 'bg-accent-bar'}"
					style="width: {pct}%"
				></div>
			</div>
		</div>

		<p
			class="nums inline-flex shrink-0 items-center gap-1 rounded-full border border-milestone-border bg-milestone-soft px-3 py-1.5 text-xs font-extrabold text-milestone-ink sm:text-sm"
		>
			<Lightning size={15} weight="fill" aria-hidden="true" />
			{xp} XP
		</p>
	</div>
</div>
