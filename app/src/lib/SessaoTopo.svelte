<script>
	import { Lightning, X } from 'phosphor-svelte';

	// No celular só cabem `tituloCurto` e a porcentagem: com o detalhe na mesma
	// linha, o título das Discursivas sumia e o texto invadia o XP em 360 px.
	let { titulo, tituloCurto = titulo, detalhe = '', progresso = 0, concluida = false, xp = 0, sequencia = 0, aoFechar } = $props();

	// posição real da sessão em % (por questões respondidas/concluídas) —
	// substitui a etiqueta decorativa fixa antiga e evita pintar 100% verde
	// antes de o aluno responder a última questão.
	let pct = $derived(Math.min(100, Math.max(0, Math.round(progresso * 100))));
	let verde = $derived(concluida && pct >= 100);
</script>

<div class="superficie rounded-3xl px-4 py-3.5 sm:px-5 sm:py-4">
	<div class="flex items-center gap-3">
		<button
			type="button"
			onclick={aoFechar}
			aria-label="Encerrar sessão"
			class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-line bg-paper text-ink-soft transition-colors hover:border-line-strong hover:text-ink active:scale-95"
		>
			<X size={19} weight="bold" aria-hidden="true" />
		</button>

		<div class="min-w-0 flex-1">
			<div class="flex items-baseline justify-between gap-2">
				<p class="truncate font-display text-sm font-bold text-ink sm:text-[15px]">
					<span class="sm:hidden">{tituloCurto}</span><span class="hidden sm:inline">{titulo}</span>
				</p>
				<p class="nums shrink-0 text-xs font-semibold text-ink-soft">
					{#if detalhe}<span class="hidden sm:inline">{detalhe} ·{' '}</span>{/if}{pct}%
				</p>
			</div>
			<div class="relative mt-2">
				<div
					class="h-2.5 overflow-hidden rounded-full bg-track"
					role="progressbar"
					aria-label="Progresso da sessão"
					aria-valuemin="0"
					aria-valuemax="100"
					aria-valuenow={pct}
				>
					<div
						class="h-full rounded-full transition-[width,background-color] duration-300 ease-out {verde
							? 'bg-ok-solid'
							: 'bg-accent-bar'}"
						style="width: {pct}%"
					></div>
				</div>
				{#if sequencia >= 3}
					<!-- marco na ponta da barra enquanto a sequência de acertos está viva -->
					<svg
						width="14"
						height="16"
						viewBox="-7 -8 14 16"
						class="absolute top-1/2 -mt-2 -ml-[7px] transition-[left] duration-300 ease-out"
						style="left: {Math.min(98, Math.max(2, pct))}%"
						aria-hidden="true"
					>
						<path d="M0 -7 L6 0 L0 7 L-6 0 Z" fill="var(--milestone)" stroke="var(--card)" stroke-width="1.5" />
					</svg>
				{/if}
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
