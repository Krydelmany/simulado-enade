<script module>
	// Coreografia em ms (~1,5 s no total). O ato 1 mora em `EscadaMarco`.
	const CONTAGEM = 260;
	const LINHA = 340;
	const BARRAS = 460;
	const FRASE = 720;
	const PULSO = 850;
	const BOTOES = 900;

	const FRASES = {
		excelente: 'Alto da escada. Dá para subir a régua.',
		solido: 'Subida firme. O próximo degrau já está marcado.',
		construcao: 'Obra em andamento. Cada erro revisado vira degrau.'
	};

	// `altura` repete o que a cor diz: quem não distingue verde de vermelho lê a linha
	const STATUS = {
		certa: { classe: 'bg-ok-solid', altura: 100, um: 'certa', varios: 'certas' },
		parcial: { classe: 'bg-warn-line', altura: 70, um: 'parcial', varios: 'parciais' },
		errada: { classe: 'bg-bad-solid', altura: 44, um: 'errada', varios: 'erradas' },
		pulada: { classe: 'bg-line-strong', altura: 20, um: 'pulada', varios: 'puladas' },
		branco: { classe: 'bg-line-strong', altura: 20, um: 'em branco', varios: 'em branco' },
		pendente: { classe: 'bg-line-strong', altura: 70, um: 'a avaliar', varios: 'a avaliar' }
	};
	const ORDEM = Object.keys(STATUS);

	/**
	 * Marca em cada item se ele faz parte de 3+ acertos seguidos. Pulada não
	 * quebra, como no selo ao vivo (`sequenciaAtual`).
	 */
	function comSequencias(itens) {
		const saida = itens.map((it) => ({ ...it, fio: '' }));
		let maior = 0;
		let n = 0;
		let de = 0;
		let ate = -1;
		for (let k = 0; k <= saida.length; k++) {
			const status = saida[k]?.status;
			if (status === 'pulada') continue;
			if (status === 'certa') {
				if (!n) de = k;
				n++;
				ate = k;
				continue;
			}
			maior = Math.max(maior, n);
			if (n >= 3) for (let j = de; j <= ate; j++) saida[j].fio = j < ate ? 'meio' : 'fim';
			n = 0;
		}
		return { itens: saida, maior };
	}
</script>

<script>
	import { onMount } from 'svelte';
	import BarrasArea from './BarrasArea.svelte';
	import Contador from './Contador.svelte';
	import EscadaMarco from './EscadaMarco.svelte';
	import { animar, mola } from './motion.js';
	import { faixaDesempenho } from './sessao.js';
	import { Lightning } from 'phosphor-svelte';

	/**
	 * Palco do Resumo (Treino, Estudo, Simulado e POO), em três atos: a escada é
	 * desenhada e o marco sobe; o placar conta enquanto a linha da sessão acende
	 * questão a questão; o marco pulsa e os botões entram. Tocar no palco pula
	 * para o fim.
	 *
	 * Só desenha: placar, métricas e regras de nota vêm prontos da rota.
	 *  - `blocos`: `[{ itens: [{ status }] }]`, a linha da sessão por parte da
	 *    prova. Bloco com `foraDaNota` aparece na linha e não entra na escada
	 *    (a discursiva do simulado).
	 *  - `metricas`: `[{ rotulo, valor, prefixo?, sufixo?, xp? }]`; número conta,
	 *    texto (tempo) entra pronto.
	 *  - `grupos`: barras que fazem parte do placar (FG e CE no simulado). As de
	 *    matéria ficam fora, depois do palco: o próximo passo tem de caber na
	 *    primeira tela do celular.
	 *  - `completa`: todas as questões da sessão foram respondidas.
	 *  - `acoes(faixa)`: botões, filhos diretos, para entrarem um a um.
	 */
	let {
		etiqueta,
		titulo,
		nivelTitulo = 'h2',
		certas,
		total,
		rotulo,
		blocos = [],
		sequencias = false,
		metricas = [],
		grupos = [],
		completa = false,
		animado = true,
		detalhe = null,
		extra = null,
		acoes = null
	} = $props();

	let contados = $derived(blocos.filter((b) => !b.foraDaNota).flatMap((b) => b.itens));
	let meios = $derived(contados.filter((it) => it.status === 'parcial').length);
	// parcial vale meio degrau, como vale meio ponto no XP
	let pct = $derived(total ? ((certas + meios * 0.5) / total) * 100 : 0);
	let faixa = $derived(faixaDesempenho(pct));
	let pulso = $derived(total > 0 && (pct >= 70 || completa));

	let linha = $derived(
		blocos.map((b) => ({ ...b, ...(sequencias ? comSequencias(b.itens) : { maior: 0 }) }))
	);
	let quantas = $derived(contados.length + blocos.filter((b) => b.foraDaNota).flatMap((b) => b.itens).length);
	let maiorSequencia = $derived(Math.max(0, ...linha.map((b) => b.maior)));
	let legenda = $derived(
		ORDEM.map((s) => ({ ...STATUS[s], s, n: contados.filter((it) => it.status === s).length })).filter((l) => l.n)
	);

	let raiz;
	// lido uma vez: quem reabre o resultado vê o palco pronto, sem refazer a cena
	// svelte-ignore state_referenced_locally
	let pulado = $state(!animado);
	// O resumo troca de lugar com o botão que o abriu: sem esta folga, o segundo
	// toque de um duplo toque caía em "Nova sessão" e o resumo sumia.
	let liberado = $state(false);

	onMount(() => {
		const t = setTimeout(() => (liberado = true), 350);
		if (animado && raiz) encenar();
		return () => clearTimeout(t);
	});

	function encenar() {
		const todos = (s) => [...raiz.querySelectorAll(s)];
		const sobe = { opacity: [0, 1], transform: ['translateY(10px)', 'translateY(0px)'] };

		animar(raiz.querySelector('[data-placar]'), { opacity: [0, 1] }, { duracao: 160, atraso: CONTAGEM - 80 });

		// cascata: a linha inteira acende em ~0,5 s, com 3 ou com 46 questões
		const celulas = todos('[data-celula]');
		const passo = Math.min(55, 480 / Math.max(1, celulas.length));
		celulas.forEach((el, k) =>
			animar(
				el,
				{ opacity: [0, 1], transform: ['scaleY(0)', 'scaleY(1)'] },
				{ ...mola(300, 18), atraso: LINHA + k * passo }
			)
		);
		todos('[data-fio]').forEach((el, k) =>
			animar(el, { opacity: [0, 1] }, { duracao: 200, atraso: LINHA + 420 + k * 18 })
		);
		todos('[data-sobe]').forEach((el, k) => animar(el, sobe, { duracao: 260, atraso: LINHA + 60 + k * 60 }));
		animar(raiz.querySelector('[data-frase]'), sobe, { duracao: 260, atraso: FRASE });

		// `visibility` junto: botão ainda invisível não recebe toque nem foco
		todos('[data-ato3] > *').forEach((el, k) =>
			animar(
				el,
				{
					visibility: ['hidden', 'visible'],
					opacity: [0, 1],
					transform: ['translateY(16px) scale(0.97)', 'translateY(0px) scale(1)']
				},
				{ ...mola(320, 24), atraso: BOTOES + k * 70 }
			)
		);
	}

	// Pula a cena: termina o que estiver animando e fixa a contagem no valor.
	function pular() {
		if (pulado) return;
		pulado = true;
		for (const a of raiz?.getAnimations?.({ subtree: true }) ?? []) {
			try {
				a.finish();
			} catch {
				// animação infinita não tem fim para pular
			}
		}
	}
</script>

<section
	bind:this={raiz}
	onpointerdown={pular}
	class="folha curso-halo relative overflow-clip rounded-3xl px-5 pt-6 pb-6 sm:p-8"
	class:pointer-events-none={!liberado}
	aria-label="Resumo: {certas} de {total}, {rotulo}"
>
	<p class="text-label font-bold text-pretty text-accent-ink">{etiqueta}</p>

	<div class="mt-1 flex items-end gap-2 sm:gap-6">
		<div class="min-w-0 flex-1 self-stretch">
			<svelte:element this={nivelTitulo} class="font-display text-title font-extrabold tracking-tight text-ink">
				{titulo}
			</svelte:element>
			<p
				data-placar
				class="nums mt-4 font-display text-6xl leading-none font-extrabold tracking-tight text-ink sm:mt-8 sm:text-8xl"
			>
				<Contador valor={certas} atraso={CONTAGEM} duracao={620} pular={pulado} /><span
					class="text-2xl font-bold text-ink-soft sm:text-4xl">/{total}</span
				>
			</p>
			<p class="mt-2 text-sm text-pretty text-ink-soft">{rotulo}</p>
			{@render detalhe?.()}
		</div>
		<EscadaMarco {pct} {pulso} {animado} tempoPulso={PULSO} classe="-mr-1 w-[8.5rem] shrink-0 sm:w-60" />
	</div>

	{#if total > 0}
		<p data-frase class="mt-3 font-display text-heading font-bold text-pretty text-ink">{FRASES[faixa]}</p>
	{/if}

	{#if quantas}
		<!-- linha viva da sessão: uma coluna por questão, na ordem em que aconteceu -->
		<div class="mt-5 flex items-end gap-2" aria-hidden="true">
			{#each linha as b, j (j)}
				<div
					class="grid min-w-0 items-end gap-x-0.5 gap-y-2 sm:gap-x-1"
					style="flex: {b.itens.length} 1 0; grid-template-columns: repeat({Math.min(46, b.itens.length)}, minmax(0, 3rem))"
				>
					{#each b.itens as it, k (k)}
						<div class="min-w-0">
							<div class="flex h-10 items-end">
								<div
									data-celula
									class="chanfro w-full origin-bottom {STATUS[it.status].classe}"
									style="height: {STATUS[it.status].altura}%"
								></div>
							</div>
							{#if sequencias}
								<!-- fio âmbar sob 3+ acertos seguidos -->
								<div
									data-fio={it.fio ? '' : undefined}
									class="mt-1 h-1 {it.fio ? 'bg-milestone' : ''} {it.fio === 'meio' ? '-mr-0.5 sm:-mr-1' : ''}"
								></div>
							{/if}
						</div>
					{/each}
				</div>
			{/each}
		</div>
		<ul class="nums mt-2.5 flex flex-wrap gap-x-4 gap-y-1 text-xs font-semibold text-ink-soft" data-sobe>
			{#each legenda as l (l.s)}
				<li class="flex items-center gap-1.5">
					<span class="chanfro h-3 w-2 {l.classe}" aria-hidden="true"></span>
					{l.n} {l.n === 1 ? l.um : l.varios}
				</li>
			{/each}
			{#if maiorSequencia >= 3}
				<li class="flex items-center gap-1.5 text-milestone-ink">
					<span class="h-1 w-3 bg-milestone" aria-hidden="true"></span>
					melhor sequência: {maiorSequencia}
				</li>
			{/if}
		</ul>
	{/if}

	{#if metricas.length}
		<dl class="mt-5 grid auto-cols-fr grid-flow-col divide-x divide-line border-y border-line py-3.5" data-sobe>
			{#each metricas as m (m.rotulo)}
				<div class="px-3 first:pl-0 last:pr-0">
					<dt class="text-xs font-medium text-ink-soft">{m.rotulo}</dt>
					<dd
						class="nums mt-0.5 flex items-center gap-1 font-display text-xl font-extrabold {m.xp
							? 'text-milestone-ink'
							: 'text-ink'}"
					>
						{#if m.xp}<Lightning size={17} weight="fill" class="shrink-0 text-milestone" aria-hidden="true" />{/if}
						<span>
							{m.prefixo ?? ''}{#if typeof m.valor === 'number'}<Contador
									valor={m.valor}
									atraso={CONTAGEM + 120}
									duracao={620}
									pular={pulado}
								/>{:else}{m.valor}{/if}{m.sufixo ?? ''}
						</span>
					</dd>
				</div>
			{/each}
		</dl>
	{/if}

	{#if grupos.length}
		<div class="mt-5">
			<BarrasArea linhas={grupos} {animado} atraso={BARRAS} grossa />
		</div>
	{/if}

	<div class="mt-6 space-y-2.5" data-ato3>
		{@render extra?.()}
		{@render acoes?.(faixa)}
	</div>
</section>

<style>
	/* canto superior cortado, como as barras da marca */
	.chanfro {
		clip-path: polygon(0 min(5px, 40%), min(5px, 60%) 0, 100% 0, 100% 100%, 0 100%);
	}
</style>
