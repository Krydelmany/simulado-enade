<script>
	import { fly } from 'svelte/transition';
	import { rotuloQuestao } from './banco.js';
	import { DUR } from './motion.js';
	import { CheckCircle, Image as ImageIcon, Info, MinusCircle, XCircle } from 'phosphor-svelte';

	let { q, onResponder } = $props();
	let escolha = $state(null);
	let respondida = $state(false);
	let mostrouPadrao = $state(false);

	const LETRAS = ['A', 'B', 'C', 'D', 'E'];

	function responder(letra) {
		if (respondida) return;
		escolha = letra;
		respondida = true;
		const certa = q.gabarito !== 'ANULADA' && letra === q.gabarito;
		onResponder?.({ id: q.id, certa, anulada: q.gabarito === 'ANULADA' });
	}

	function autoavaliar(nivel) {
		respondida = true;
		onResponder?.({ id: q.id, certa: nivel === 1, parcial: nivel === 0.5 });
	}

	function classeAlt(letra) {
		const base =
			'flex w-full items-start gap-3 rounded-2xl border-2 p-3.5 text-left text-[15px] leading-relaxed transition-[border-color,background-color,color,transform] duration-150 active:scale-[0.99] disabled:cursor-default ';
		if (!respondida)
			return base + 'border-slate-300 bg-white hover:border-ink hover:bg-slate-50';
		if (q.gabarito === 'ANULADA') return base + 'border-slate-300 bg-slate-100';
		if (letra === q.gabarito) return base + 'border-emerald-700 bg-emerald-700 text-white';
		if (letra === escolha) return base + 'border-rose-700 bg-rose-700 text-white';
		return base + 'border-slate-200 bg-white opacity-50';
	}
</script>

<article in:fly={{ x: 28, duration: DUR }} class="rounded-3xl bg-white p-4 shadow-[0_10px_30px_-12px_rgba(20,33,61,0.25)] sm:p-6">
	<p class="text-[11px] font-bold tracking-[0.14em] text-accent-deep uppercase">
		{rotuloQuestao(q)}
	</p>
	<h2 class="mt-1 text-base font-bold tracking-tight">{q.tema}</h2>

	{#if q.figura}
		<p class="mt-3 flex items-start gap-2 rounded-2xl border border-dashed border-amber-500 bg-amber-50 p-3 text-sm text-amber-900">
			<ImageIcon size={18} weight="bold" aria-hidden="true" class="mt-0.5 shrink-0" />
			<span>Figura: {q.figura.desc} <span class="italic">(imagem entra aqui)</span></span>
		</p>
	{/if}

	<div class="enunciado mt-3 max-w-[65ch] text-[15px] leading-relaxed">{q.enunciado}</div>

	{#if q.tipo === 'objetiva'}
		<div class="mt-4 space-y-2" role="group" aria-label="Alternativas">
			{#each LETRAS as letra, k (letra)}
				{#if q.alternativas[letra]}
					<div class="rise" style="animation-delay: {k * 45}ms">
						<button type="button" onclick={() => responder(letra)} disabled={respondida} class={classeAlt(letra)}>
							<span
								class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-sm font-extrabold {respondida &&
								(letra === q.gabarito || letra === escolha)
									? 'bg-white/25'
									: 'bg-slate-200/70 text-ink'}"
							>
								{letra}
							</span>
							<span class="enunciado">{q.alternativas[letra]}</span>
						</button>
					</div>
				{/if}
			{/each}
		</div>
		{#if respondida}
			<p
				in:fly={{ y: 8, duration: DUR }}
				class="mt-3 flex items-start gap-2 rounded-2xl p-3.5 text-sm font-semibold {q.gabarito === 'ANULADA' || escolha === q.gabarito
					? 'bg-emerald-50 text-emerald-900'
					: 'bg-rose-50 text-rose-900'}"
				role="status"
			>
				{#if q.gabarito === 'ANULADA'}
					<Info size={19} weight="bold" aria-hidden="true" class="mt-0.5 shrink-0" />
					<span>Questão anulada pelo INEP — ponto para todos.</span>
				{:else if escolha === q.gabarito}
					<CheckCircle size={19} weight="bold" aria-hidden="true" class="mt-0.5 shrink-0" />
					<span>Certa. Gabarito: {q.gabarito}</span>
				{:else}
					<XCircle size={19} weight="bold" aria-hidden="true" class="mt-0.5 shrink-0" />
					<span>Não foi dessa vez. Gabarito: {q.gabarito} — você marcou {escolha}.</span>
				{/if}
			</p>
		{/if}
	{:else}
		<div class="mt-4">
			{#if !mostrouPadrao}
				<button
					type="button"
					onclick={() => (mostrouPadrao = true)}
					class="w-full rounded-2xl bg-ink p-3.5 font-bold text-white transition-transform hover:bg-ink-soft active:scale-[0.98]"
				>
					Escrevi minha resposta — ver padrão oficial
				</button>
			{:else}
				<div in:fly={{ y: 8, duration: DUR }} class="rounded-2xl border border-slate-300 bg-slate-50 p-4">
					<p class="text-[11px] font-bold tracking-[0.14em] text-ink-soft uppercase">
						Padrão de resposta · INEP
					</p>
					<p class="enunciado mt-2 max-w-[65ch] text-sm leading-relaxed">{q.padrao}</p>
				</div>
				{#if !respondida}
					<p class="mt-3 text-sm font-bold">Compare com a sua. Como foi?</p>
					<div class="mt-2 grid grid-cols-3 gap-2">
						<button
							type="button"
							onclick={() => autoavaliar(1)}
							class="flex items-center justify-center gap-1.5 rounded-2xl bg-emerald-700 p-3 text-sm font-bold text-white transition-transform active:scale-[0.97]"
						>
							<CheckCircle size={17} weight="bold" aria-hidden="true" /> Acertei
						</button>
						<button
							type="button"
							onclick={() => autoavaliar(0.5)}
							class="flex items-center justify-center gap-1.5 rounded-2xl bg-amber-500 p-3 text-sm font-bold text-white transition-transform active:scale-[0.97]"
						>
							<MinusCircle size={17} weight="bold" aria-hidden="true" /> Meio
						</button>
						<button
							type="button"
							onclick={() => autoavaliar(0)}
							class="flex items-center justify-center gap-1.5 rounded-2xl bg-rose-700 p-3 text-sm font-bold text-white transition-transform active:scale-[0.97]"
						>
							<XCircle size={17} weight="bold" aria-hidden="true" /> Errei
						</button>
					</div>
				{/if}
			{/if}
		</div>
	{/if}
</article>
