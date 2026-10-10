<script>
	import { Lightning, X } from 'phosphor-svelte';

	let { titulo, detalhe = '', progresso = 0, xp = 0, aoFechar } = $props();
</script>

<div class=" -mx-4 -mt-6 bg-bar px-4 pt-4 pb-5 text-white" style="border-radius: 0 0 26px 26px;">
	<div class="mx-auto max-w-3xl">
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
			<p class="text-[17px] font-bold">{titulo}</p>
			{#if detalhe}
				<p class="shrink-0 text-sm font-medium text-bar-fg">{detalhe}</p>
			{/if}
		</div>
		<div
			class="mt-2 h-2.5 overflow-hidden rounded-full bg-white/15"
			role="progressbar"
			aria-label="Progresso da sessão"
			aria-valuemin="0"
			aria-valuemax="100"
			aria-valuenow={Math.round(progresso * 100)}
		>
			<div
				class="h-full rounded-full bg-accent transition-[width] duration-500 ease-out"
				style="width: {Math.round(progresso * 100)}%"
			></div>
		</div>
	</div>
</div>
