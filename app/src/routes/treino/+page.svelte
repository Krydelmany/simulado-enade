<script>
	import { onMount } from 'svelte';
	import Questao from '$lib/Questao.svelte';
	import Contador from '$lib/Contador.svelte';
	import { carregarBanco, embaralhar } from '$lib/banco.js';
	import { somarXP, registrarAtividade, registrarErro, removerErro } from '$lib/stats.js';
	import { ArrowLeft, ArrowRight, Flag, Tag, Timer, Trophy } from 'phosphor-svelte';

	let banco = $state([]);
	let carregou = $state(false);
	let falhou = $state(false);
	let fila = $state([]);
	let i = $state(0);
	let certas = $state(0);
	let feitas = $state(0);
	let tema = $state('todos');
	let encerrada = $state(false);
	let inicio = $state(Date.now());
	let xpGanho = $state(0);

	let temas = $derived([...new Set(banco.map((q) => q.tema))].sort());

	onMount(async () => {
		try {
			banco = await carregarBanco();
		} catch {
			falhou = true;
		} finally {
			carregou = true;
		}
		fila = embaralhar(banco);
	});

	function aplicarTema() {
		fila = embaralhar(tema === 'todos' ? banco : banco.filter((q) => q.tema === tema));
		i = 0;
		certas = 0;
		feitas = 0;
		xpGanho = 0;
		encerrada = false;
		inicio = Date.now();
	}

	function aoResponder(r) {
		feitas++;
		registrarAtividade();
		if (r.certa) {
			certas++;
			somarXP(10);
			xpGanho += 10;
			removerErro(r.id);
		} else if (!r.anulada) {
			registrarErro(r.id);
		}
	}

	function minutos() {
		return Math.max(1, Math.round((Date.now() - inicio) / 60000));
	}
</script>

<div class="mb-4 flex items-center gap-2">
	<a href="/" class="flex items-center gap-1 rounded-lg px-2 py-2 text-sm font-bold text-ink-soft" aria-label="Voltar ao início">
		<ArrowLeft size={18} weight="bold" aria-hidden="true" /> Início
	</a>
	<span class="flex-1"></span>
	<h1 class="text-sm font-bold tracking-wide text-ink-soft uppercase">Treino livre</h1>
</div>

{#if !carregou}
	<div class="space-y-3" role="status" aria-label="Carregando questões">
		<div class="h-40 animate-pulse rounded-3xl bg-white"></div>
		<div class="h-14 animate-pulse rounded-2xl bg-white"></div>
		<div class="h-14 animate-pulse rounded-2xl bg-white"></div>
	</div>
{:else if falhou || !banco.length}
	<div class="rounded-3xl bg-white p-6 text-center shadow-sm" role="alert">
		<p class="text-lg font-bold">Não deu para carregar as questões</p>
		<p class="mt-1 text-sm text-ink-soft">Verifique sua conexão e tente de novo.</p>
		<button type="button" onclick={() => location.reload()} class="mt-4 w-full rounded-2xl bg-ink p-3.5 font-bold text-white transition-transform active:scale-[0.98]">
			Tentar de novo
		</button>
	</div>
{:else if encerrada}
	<div class="rise space-y-4 rounded-3xl bg-white p-6 text-center shadow-[0_10px_30px_-12px_rgba(20,33,61,0.25)]">
		<p class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-soft">
			<Trophy size={28} weight="bold" aria-hidden="true" class="text-accent-deep" />
		</p>
		<h2 class="text-lg font-bold">Resumo da sessão</h2>
		<p class="text-6xl font-extrabold tracking-tight text-ink nums">
			<Contador valor={certas} />/{feitas}
		</p>
		<div class="mx-auto grid max-w-xs grid-cols-3 gap-2 text-center">
			<div class="rounded-2xl bg-paper p-3">
				<p class="nums text-xl font-extrabold">{feitas ? Math.round((certas / feitas) * 100) : 0}%</p>
				<p class="text-[11px] font-semibold text-ink-soft">acerto</p>
			</div>
			<div class="rounded-2xl bg-paper p-3">
				<p class="nums flex items-center justify-center gap-1 text-xl font-extrabold">
					<Timer size={17} weight="bold" aria-hidden="true" />{minutos()}
				</p>
				<p class="text-[11px] font-semibold text-ink-soft">min</p>
			</div>
			<div class="rounded-2xl bg-paper p-3">
				<p class="nums text-xl font-extrabold">+{xpGanho}</p>
				<p class="text-[11px] font-semibold text-ink-soft">XP</p>
			</div>
		</div>
		{#if tema !== 'todos'}
			<p class="text-sm text-ink-soft">Tema: {tema}</p>
		{/if}
		<button type="button" onclick={aplicarTema} class="w-full rounded-2xl bg-ink p-3.5 font-bold text-white transition-transform active:scale-[0.98]">
			Nova sessão
		</button>
	</div>
{:else}
	<div class="mb-3 flex items-center gap-2">
		<label class="flex flex-1 items-center gap-2 rounded-2xl border border-slate-300 bg-white px-3">
			<Tag size={17} weight="bold" aria-hidden="true" class="shrink-0 text-ink-soft" />
			<span class="sr-only">Filtrar por tema</span>
			<select bind:value={tema} onchange={aplicarTema} class="w-full bg-transparent py-3 text-sm font-semibold text-ink">
				<option value="todos">Todos os temas</option>
				{#each temas as t (t)}
					<option value={t}>{t}</option>
				{/each}
			</select>
		</label>
		<button
			type="button"
			onclick={() => (encerrada = true)}
			class="flex items-center gap-1.5 rounded-2xl bg-ink px-4 py-3 text-sm font-bold text-white transition-transform active:scale-[0.97]"
		>
			<Flag size={17} weight="bold" aria-hidden="true" /> Parar
		</button>
	</div>

	<p class="nums mb-3 text-center text-sm font-bold text-ink-soft">
		{i + 1}ª questão · {certas}/{feitas} certas
	</p>

	{#if fila[i]}
		{#key fila[i].id + '-' + i}
			<Questao q={fila[i]} onResponder={aoResponder} />
		{/key}
		<div class="mt-3">
			<button
				type="button"
				onclick={() => (i = (i + 1) % fila.length)}
				class="flex w-full items-center justify-center gap-2 rounded-2xl bg-ink p-3.5 font-bold text-white transition-transform active:scale-[0.98]"
			>
				Próxima <ArrowRight size={18} weight="bold" aria-hidden="true" />
			</button>
		</div>
	{/if}
{/if}
