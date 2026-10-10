<script>
	import { fly } from 'svelte/transition';
	import { rotuloQuestao } from './banco.js';
	import { DUR } from './motion.js';
	import {
		Atom,
		CheckCircle,
		Image as ImageIcon,
		Info,
		MinusCircle,
		SealCheck,
		XCircle
	} from 'phosphor-svelte';

	let { q, onResponder } = $props();
	let escolha = $state(null);
	let respondida = $state(false);
	let mostrouPadrao = $state(false);

	const LETRAS = ['A', 'B', 'C', 'D', 'E'];
	const acertou = $derived(respondida && q.gabarito !== 'ANULADA' && escolha === q.gabarito);
	const errou = $derived(respondida && q.gabarito !== 'ANULADA' && escolha !== q.gabarito);

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
		if (!respondida) return base + 'border-line bg-card hover:border-ink';
		if (q.gabarito === 'ANULADA') return base + 'border-line bg-tile';
		if (letra === q.gabarito) return base + 'border-ok-solid bg-ok-solid text-white pop';
		if (letra === escolha) return base + 'border-bad-solid bg-bad-solid text-white';
		return base + 'border-line bg-card opacity-50';
	}
</script>

<article in:fly={{ x: 28, duration: DUR }} class="rounded-3xl bg-card p-4 shadow-[0_10px_30px_-12px_rgba(20,33,61,0.25)] sm:p-6">
	<div class="flex flex-wrap items-center gap-2">
		<p class="text-[11px] font-bold tracking-[0.14em] text-accent-ink uppercase">
			{rotuloQuestao(q)}
		</p>
		{#if q.materia_ava}
			<p class="flex items-center gap-1 rounded-full bg-accent-soft px-2.5 py-0.5 text-[11px] font-bold text-accent-ink">
				<Atom size={12} weight="bold" aria-hidden="true" />
				{q.materia_ava}
			</p>
		{/if}
		{#if q.parte}
			<p class="rounded-full border border-line px-2.5 py-0.5 text-[11px] font-bold text-ink-soft">
				{q.parte === 'FG' ? 'Formação Geral' : q.parte}
			</p>
		{/if}
	</div>
	<h2 class="mt-1 text-base font-bold tracking-tight">{q.tema}</h2>

	{#if q.imagem}
		<figure class="mt-3 overflow-hidden rounded-2xl border border-line bg-white">
			<img src={q.imagem.src} alt={q.imagem.alt} loading="lazy" class="h-auto w-full" />
			{#if q.imagem.legenda}
				<figcaption class="px-3 py-2 text-xs text-ink-soft">{q.imagem.legenda}</figcaption>
			{/if}
		</figure>
	{:else if q.figura}
		<p class="mt-3 flex items-start gap-2 rounded-2xl border border-dashed border-warn-line bg-warn-bg p-3 text-sm text-warn-fg">
			<ImageIcon size={18} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
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
									: 'bg-chip text-ink'}"
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
				class="mt-3 flex items-start gap-2 rounded-2xl p-3.5 text-sm font-semibold {errou
					? 'shake bg-bad-bg text-bad-fg'
					: 'bg-ok-bg text-ok-fg'}"
				role="status"
			>
				{#if q.gabarito === 'ANULADA'}
					<Info size={19} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
					<span>Questão anulada pelo INEP — ponto para todos.</span>
				{:else if acertou}
					<CheckCircle size={19} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
					<span>Certa. Gabarito: {q.gabarito}</span>
				{:else}
					<XCircle size={19} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
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
					class="btn3d duo-accent w-full rounded-2xl p-3.5 font-bold"
				>
					Escrevi minha resposta — ver padrão oficial
				</button>
			{:else}
				<div in:fly={{ y: 8, duration: DUR }} class="rounded-2xl border border-line bg-panel p-4">
					<p class="flex items-center gap-1.5 text-[11px] font-bold tracking-[0.14em] text-ink-soft uppercase">
						<SealCheck size={15} weight="bold" aria-hidden="true" />
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
							class="btn3d flex items-center justify-center gap-1.5 rounded-2xl border-ok-solid bg-ok-solid p-3 text-sm font-bold text-white"
						>
							<CheckCircle size={17} weight="bold" aria-hidden="true" /> Acertei
						</button>
						<button
							type="button"
							onclick={() => autoavaliar(0.5)}
							class="btn3d flex items-center justify-center gap-1.5 rounded-2xl border-amber-600 bg-amber-500 p-3 text-sm font-bold text-white"
						>
							<MinusCircle size={17} weight="bold" aria-hidden="true" /> Meio
						</button>
						<button
							type="button"
							onclick={() => autoavaliar(0)}
							class="btn3d flex items-center justify-center gap-1.5 rounded-2xl border-bad-solid bg-bad-solid p-3 text-sm font-bold text-white"
						>
							<XCircle size={17} weight="bold" aria-hidden="true" /> Errei
						</button>
					</div>
				{/if}
			{/if}
		</div>
	{/if}
</article>
