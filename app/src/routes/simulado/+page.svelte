<script>
	import { onMount } from 'svelte';
	import { carregarBanco, ehGerada } from '$lib/banco.js';
	import { getErros } from '$lib/stats.js';
	import {
		ArrowLeft,
		ArrowRight,
		ArrowsClockwise,
		Database,
		Infinity as InfinityIcon,
		Stairs,
		Timer
	} from 'phosphor-svelte';

	// Formato oficial da prova 2026 (Portaria INEP nº 161).
	const FORMATO = [
		{ label: 'Formação Geral', valor: '15 objetivas' },
		{ label: 'Componente Específico', valor: '30 objetivas' },
		{ label: 'Discursiva', valor: '1 questão' },
		{ label: 'Tempo', valor: '4 horas' }
	];

	// Meta do banco = prova completa (15 + 30 + 1).
	const META = 160;

	let total = $state(0);
	let obj = $state(0);
	let disc = $state(0);
	let erros = $state(0);
	let pronto = $state(false);

	let pct = $derived(Math.min(100, Math.round((total / META) * 100)));

	onMount(async () => {
		try {
			// o simulado é a prova: as questões geradas para revisão não contam
			const b = (await carregarBanco()).filter((q) => !ehGerada(q));
			total = b.length;
			obj = b.filter((q) => q.tipo === 'objetiva').length;
			disc = b.filter((q) => q.tipo === 'discursiva').length;
		} finally {
			erros = getErros().length;
			pronto = true;
		}
	});
</script>

<div class="mx-auto w-full max-w-3xl">
	<div class="mb-5 flex items-center gap-2">
		<a
			href="/"
			class="flex min-h-11 items-center gap-1 rounded-lg px-2 text-sm font-bold text-ink-soft hover:text-ink"
			aria-label="Voltar ao início"
		>
			<ArrowLeft size={18} weight="bold" aria-hidden="true" /> Início
		</a>
		<span class="flex-1"></span>
		<h1 class="font-code text-label font-bold text-ink-soft uppercase">Simulado real</h1>
	</div>

	<div class="space-y-4">
		<!-- Formato da prova: informação estável, não depende de rede. -->
		<section
			class="blueprint rise rounded-3xl bg-bar p-5 text-white shadow-[0_10px_30px_-12px_rgba(20,33,61,0.45)] sm:p-6"
		>
			<p class="flex items-center gap-2 font-code text-label font-bold text-bar-fg uppercase">
				<Timer size={15} weight="bold" aria-hidden="true" /> Formato ENADE 2026
			</p>
			<dl class="nums mt-4 space-y-2 text-[15px] font-semibold">
				{#each FORMATO as f, k (f.label)}
					<div
						class="flex items-baseline justify-between gap-3 {k === FORMATO.length - 1
							? 'border-t border-white/20 pt-2'
							: ''}"
					>
						<dt>{f.label}</dt>
						<dd class="text-right">{f.valor}</dd>
					</div>
				{/each}
			</dl>
			<p class="mt-4 text-xs leading-relaxed text-pretty text-bar-fg">
				São 45 objetivas e 1 discursiva em 4 horas. Fonte: Portaria INEP nº 161.
			</p>
		</section>

		<!-- Estado real: o que já existe no banco para montar a prova. -->
		<section
			class="rise rounded-3xl border border-line bg-card p-5 shadow-sm sm:p-6"
			style="animation-delay: 80ms"
			aria-label="Estado do banco de questões"
		>
			<div class="flex items-center gap-2">
				<Database size={18} weight="bold" class="text-accent-ink" aria-hidden="true" />
				<h2 class="font-display text-heading font-bold">Estado do banco</h2>
			</div>

			{#if !pronto}
				<div class="mt-4 space-y-3" role="status" aria-label="Carregando o estado do banco">
					<div class="h-5 w-56 animate-pulse rounded-lg bg-skel"></div>
					<div class="h-3 w-full animate-pulse rounded-full bg-skel"></div>
				</div>
			{:else}
				<p class="nums mt-3 text-sm text-ink-soft">
					{total} de {META} questões ({obj} objetivas + {disc} discursivas)
				</p>
				<div
					class="mt-3 h-3 overflow-hidden rounded-full border border-line bg-track"
					role="progressbar"
					aria-valuenow={total}
					aria-valuemin="0"
					aria-valuemax={META}
					aria-label="Progresso do banco de questões"
				>
					<div
						class="h-full rounded-full bg-accent-bar transition-[width] duration-700 ease-out"
						style="width: {pct}%"
					></div>
				</div>

				{#if total === 0}
					<p
						class="mt-4 rounded-2xl border border-dashed border-warn-line bg-warn-bg p-3 text-xs leading-relaxed text-warn-fg"
					>
						O banco não carregou. Verifique a conexão e
						<button type="button" class="font-bold underline" onclick={() => location.reload()}>
							recarregue a página</button
						>.
					</p>
				{:else}
					<p class="mt-3 flex items-start gap-2 text-xs leading-relaxed text-pretty text-ink-soft">
						<span class="mt-px shrink-0" aria-hidden="true">
							<Timer size={14} weight="bold" class="text-ink-soft" />
						</span>
						<span>
							O <strong class="font-bold text-ink">simulado cronometrado</strong> entra quando o banco
							estiver completo — ainda faltam {Math.max(0, META - total)} questões.
						</span>
					</p>
				{/if}
			{/if}
		</section>

		<!-- Caminhos úteis: nenhum botão morto, tudo navega. -->
		<section aria-label="Formas de treinar agora" class="space-y-3">
			<h2 class="font-display text-heading font-bold">Dá para treinar agora</h2>

			<a
				href="/treino/"
				class="rise group flex items-center gap-4 rounded-3xl border border-line bg-card p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:border-ink/25 active:scale-[0.99]"
				style="animation-delay: 120ms"
			>
				<span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-accent-soft" aria-hidden="true">
					<InfinityIcon size={24} weight="bold" class="text-accent-ink" aria-hidden="true" />
				</span>
				<span class="min-w-0 flex-1">
					<span class="block font-display text-base font-bold">Treino livre</span>
					<span class="block text-sm text-ink-soft">Questões em sequência, no seu ritmo.</span>
				</span>
				<ArrowRight
					size={20}
					weight="bold"
					class="shrink-0 text-ink-soft opacity-60 transition-transform group-hover:translate-x-1 group-hover:text-accent-ink group-hover:opacity-100"
					aria-hidden="true"
				/>
			</a>

			<a
				href="/estudo/"
				class="rise group flex items-center gap-4 rounded-3xl border border-line bg-card p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:border-ink/25 active:scale-[0.99]"
				style="animation-delay: 190ms"
			>
				<span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-accent-soft" aria-hidden="true">
					<Stairs size={24} weight="bold" class="text-accent-ink" aria-hidden="true" />
				</span>
				<span class="min-w-0 flex-1">
					<span class="block font-display text-base font-bold">Estudo por níveis</span>
					<span class="block text-sm text-ink-soft">Fácil, Médio, Difícil e ENADE oficial, por matéria.</span>
				</span>
				<ArrowRight
					size={20}
					weight="bold"
					class="shrink-0 text-ink-soft opacity-60 transition-transform group-hover:translate-x-1 group-hover:text-accent-ink group-hover:opacity-100"
					aria-hidden="true"
				/>
			</a>

			{#if pronto && erros > 0}
				<a
					href="/treino/?modo=revisao"
					class="rise group flex items-center gap-4 rounded-3xl border border-line bg-card p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:border-ink/25 active:scale-[0.99]"
					style="animation-delay: 260ms"
				>
					<span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-accent-soft" aria-hidden="true">
						<ArrowsClockwise size={24} weight="bold" class="text-accent-ink" aria-hidden="true" />
					</span>
					<span class="min-w-0 flex-1">
						<span class="block font-display text-base font-bold">Revisar erros</span>
						<span class="block text-sm text-ink-soft">{erros} questões para revisar.</span>
					</span>
					<ArrowRight
						size={20}
						weight="bold"
						class="shrink-0 text-ink-soft opacity-60 transition-transform group-hover:translate-x-1 group-hover:text-accent-ink group-hover:opacity-100"
						aria-hidden="true"
					/>
				</a>
			{/if}
		</section>
	</div>
</div>
