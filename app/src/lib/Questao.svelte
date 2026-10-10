<script>
	import { rotuloQuestao } from './banco.js';

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
		// 1 = acertei, 0.5 = meio, 0 = errei
		respondida = true;
		onResponder?.({ id: q.id, certa: nivel === 1, parcial: nivel === 0.5 });
	}

	function classeAlt(letra) {
		if (!respondida) return 'border-slate-300 bg-white active:bg-blue-50';
		if (q.gabarito === 'ANULADA') return 'border-slate-300 bg-slate-100';
		if (letra === q.gabarito) return 'border-green-600 bg-green-50 font-semibold';
		if (letra === escolha) return 'border-red-600 bg-red-50';
		return 'border-slate-200 bg-white opacity-60';
	}
</script>

<article class="rounded-xl bg-white p-4 shadow-sm sm:p-6">
	<p class="text-xs font-medium tracking-wide text-blue-800 uppercase">{rotuloQuestao(q)}</p>
	<h2 class="mt-1 text-sm font-semibold text-slate-700">{q.tema}</h2>

	{#if q.figura}
		<p class="mt-3 rounded-lg border border-dashed border-amber-400 bg-amber-50 p-3 text-sm text-amber-900">
			🖼️ Figura: {q.figura.desc} <span class="italic">(imagem entra aqui)</span>
		</p>
	{/if}

	<div class="enunciado mt-3 text-[15px] leading-relaxed">{q.enunciado}</div>

	{#if q.tipo === 'objetiva'}
		<div class="mt-4 space-y-2">
			{#each LETRAS as letra (letra)}
				{#if q.alternativas[letra]}
					<button
						type="button"
						onclick={() => responder(letra)}
						disabled={respondida}
						class="flex w-full items-start gap-3 rounded-lg border-2 p-3 text-left text-[15px] {classeAlt(
							letra
						)}"
					>
						<span class="font-bold">{letra}</span>
						<span class="enunciado">{q.alternativas[letra]}</span>
					</button>
				{/if}
			{/each}
		</div>
		{#if respondida}
			<p class="mt-3 rounded-lg p-3 text-sm font-semibold {q.gabarito === 'ANULADA' || escolha === q.gabarito ? 'bg-green-100 text-green-900' : 'bg-red-100 text-red-900'}">
				{#if q.gabarito === 'ANULADA'}
					Questão anulada pelo INEP — ponto para todos.
				{:else if escolha === q.gabarito}
					✅ Certa! Gabarito: {q.gabarito}
				{:else}
					❌ Errou. Gabarito: {q.gabarito} (você marcou {escolha})
				{/if}
			</p>
		{/if}
	{:else}
		<div class="mt-4">
			{#if !mostrouPadrao}
				<button
					type="button"
					onclick={() => (mostrouPadrao = true)}
					class="w-full rounded-lg bg-blue-900 p-3 font-semibold text-white"
				>
					Escrevi minha resposta — ver padrão oficial
				</button>
			{:else}
				<div class="rounded-lg border border-slate-300 bg-slate-50 p-3">
					<p class="text-xs font-bold tracking-wide text-slate-500 uppercase">Padrão de resposta (INEP)</p>
					<p class="enunciado mt-2 text-sm">{q.padrao}</p>
				</div>
				{#if !respondida}
					<p class="mt-3 text-sm font-medium">Compare com a sua. Como foi?</p>
					<div class="mt-2 grid grid-cols-3 gap-2">
						<button type="button" onclick={() => autoavaliar(1)} class="rounded-lg bg-green-700 p-3 font-semibold text-white">Acertei</button>
						<button type="button" onclick={() => autoavaliar(0.5)} class="rounded-lg bg-amber-500 p-3 font-semibold text-white">Meio</button>
						<button type="button" onclick={() => autoavaliar(0)} class="rounded-lg bg-red-700 p-3 font-semibold text-white">Errei</button>
					</div>
				{/if}
			{/if}
		</div>
	{/if}
</article>
