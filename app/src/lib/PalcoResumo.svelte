<script module>
	// Coreografia em ms (~1,5 s no total). O ato 1 mora em `EscadaMarco`.
	const CONTAGEM = 260;
	const LINHA = 340;
	const BARRAS = 460;
	const FRASE = 720;
	const PULSO = 850;
	const BOTOES = 900;
	// folga contra duplo toque: logo que o palco abre e logo que a cena é pulada
	const FOLGA = 350;

	// acima disto a linha agrupa questões por coluna: 156 viravam 4 fileiras e
	// empurravam os botões para fora da primeira tela do celular
	const COLUNAS = 46;

	// Placar e total por número de dígitos do total: com 3, "117/156" invadia a
	// escada em 360 px.
	const PLACAR = [
		['text-6xl sm:text-8xl', 'text-2xl sm:text-4xl'],
		['text-4xl sm:text-7xl', 'text-xl sm:text-3xl'],
		['text-3xl sm:text-6xl', 'text-sm sm:text-2xl']
	];

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

	/** Colunas de várias questões, cada uma com a fatia de cada resultado. */
	function agrupar(itens) {
		const porColuna = Math.ceil(itens.length / COLUNAS);
		const colunas = [];
		for (let k = 0; k < itens.length; k += porColuna) {
			const fatia = itens.slice(k, k + porColuna);
			colunas.push(
				ORDEM.map((s) => ({
					classe: STATUS[s].classe,
					pct: (fatia.filter((it) => it.status === s).length / fatia.length) * 100
				})).filter((parte) => parte.pct)
			);
		}
		return { porColuna, colunas };
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
	 *    prova. Bloco com `foraDaNota` (e `rotulo`) aparece na linha e na legenda,
	 *    e não entra na escada (a discursiva do simulado).
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
		blocos.map((b) => ({
			...b,
			...(sequencias ? comSequencias(b.itens) : { maior: 0 }),
			...(b.itens.length > COLUNAS ? agrupar(b.itens) : { porColuna: 1, colunas: null })
		}))
	);
	// fora da nota tem legenda própria, sem somar com as que valem: o número de
	// certas tem de bater com o placar
	let aparte = $derived(
		blocos
			.filter((b) => b.foraDaNota)
			.flatMap((b) => b.itens.map((it) => ({ ...STATUS[it.status], rotulo: b.rotulo })))
	);
	let quantas = $derived(contados.length + aparte.length);
	let porColuna = $derived(Math.max(1, ...linha.map((b) => b.porColuna)));
	let maiorSequencia = $derived(Math.max(0, ...linha.map((b) => b.maior)));
	let legenda = $derived(
		ORDEM.map((s) => ({ ...STATUS[s], s, n: contados.filter((it) => it.status === s).length })).filter((l) => l.n)
	);

	let placar = $derived(PLACAR[Math.min(2, Math.max(0, String(total).length - 2))]);
	// a métrica mais comprida manda na fonte da linha (o raio do XP ocupa ~2 dígitos)
	let larguraMetrica = $derived(
		Math.max(0, ...metricas.map((m) => `${m.prefixo ?? ''}${m.valor}${m.sufixo ?? ''}`.length + (m.xp ? 2 : 0)))
	);
	let fonteMetrica = $derived(
		larguraMetrica >= 8 ? 'text-base sm:text-xl' : larguraMetrica === 7 ? 'text-lg sm:text-xl' : 'text-xl'
	);

	let raiz;
	let refTitulo;
	// lido uma vez: quem reabre o resultado vê o palco pronto, sem refazer a cena
	// svelte-ignore state_referenced_locally
	let pulado = $state(!animado);
	// O resumo troca de lugar com o botão que o abriu: sem esta folga, o segundo
	// toque de um duplo toque caía em "Nova sessão" e o resumo sumia.
	let liberado = $state(false);
	// Botões só aceitam toque com a cena terminada. Antes, tocar na área vazia
	// para pular fazia o botão aparecer embaixo do dedo e receber o clique.
	let botoesLivres = $state(false);
	let esperaBotoes;

	function soltarBotoes(ms) {
		clearTimeout(esperaBotoes);
		botoesLivres = false;
		esperaBotoes = setTimeout(() => (botoesLivres = true), ms);
	}

	onMount(() => {
		const t = setTimeout(() => (liberado = true), FOLGA);
		soltarBotoes(FOLGA);
		// o botão que abriu o resumo sumiu: sem isto o teclado recomeçava do `body`
		refTitulo?.focus({ preventScroll: true });
		if (animado && raiz) {
			encenar();
			soltarBotoes(Math.max(FOLGA, fimDaCena()));
		}
		return () => {
			clearTimeout(t);
			clearTimeout(esperaBotoes);
		};
	});

	function animacoes() {
		return raiz?.getAnimations?.({ subtree: true }) ?? [];
	}

	/** Quando acaba a última animação do palco (as da escada já começaram). */
	function fimDaCena() {
		const fins = animacoes().map((a) => a.effect?.getComputedTiming().endTime);
		return Math.max(0, ...fins.filter(Number.isFinite));
	}

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

	// Pula a cena: termina o que estiver animando e fixa a contagem no valor. No
	// `click`, não no `pointerdown`: o toque inteiro já foi do palco, e o botão
	// que aparece no lugar dele ainda espera a folga.
	function pular(e) {
		if (pulado || e.target.closest('a, button')) return;
		pulado = true;
		const rodando = animacoes().filter((a) => a.playState === 'running');
		if (!rodando.length) return;
		soltarBotoes(FOLGA);
		for (const a of rodando) {
			try {
				a.finish();
			} catch {
				// animação infinita não tem fim para pular
			}
		}
	}
</script>

<!-- pular é só um atalho de toque: sem ele a cena termina sozinha em ~1,5 s, e o
     teclado não depende dela -->
<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
<section
	bind:this={raiz}
	onclick={pular}
	class="folha curso-halo relative overflow-clip rounded-3xl px-5 pt-6 pb-6 sm:p-8"
	class:pointer-events-none={!liberado}
	aria-label="Resumo: {certas} de {total}, {rotulo}"
>
	<p class="text-label font-bold text-pretty text-accent-ink">{etiqueta}</p>

	<div class="mt-1 flex items-end gap-2 sm:gap-6">
		<div class="min-w-0 flex-1 self-stretch">
			<svelte:element
				this={nivelTitulo}
				bind:this={refTitulo}
				tabindex="-1"
				class="titulo font-display text-title font-extrabold tracking-tight text-ink"
			>
				{titulo}
			</svelte:element>
			<p
				data-placar
				class="nums mt-4 font-display leading-none font-extrabold tracking-tight text-ink sm:mt-8 {placar[0]}"
			>
				<Contador valor={certas} atraso={CONTAGEM} duracao={620} pular={pulado} /><span
					class="font-bold text-ink-soft {placar[1]}">/{total}</span
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
		<!-- linha viva da sessão: uma coluna por questão, na ordem em que aconteceu
		     (sessão longa agrupa: cada coluna empilha as suas, com os acertos embaixo) -->
		<div class="mt-5 flex items-end gap-2" aria-hidden="true">
			{#each linha as b, j (j)}
				<div
					class="grid min-w-0 items-end gap-x-0.5 gap-y-2 sm:gap-x-1"
					style="flex: {b.itens.length} 1 0; grid-template-columns: repeat({b.colunas?.length ?? b.itens.length}, minmax(0, 3rem))"
				>
					{#each b.colunas ?? [] as partes, k (k)}
						<div data-celula class="chanfro flex h-10 min-w-0 origin-bottom flex-col-reverse">
							{#each partes as parte, n (n)}
								<div class={parte.classe} style="height: {parte.pct}%"></div>
							{/each}
						</div>
					{/each}
					{#each b.colunas ? [] : b.itens as it, k (k)}
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
			{#each aparte as l, k (k)}
				<li class="flex items-center gap-1.5">
					<span class="chanfro h-3 w-2 {l.classe}" aria-hidden="true"></span>
					{l.rotulo} {l.um}, fora da nota
				</li>
			{/each}
			{#if porColuna > 1}
				<li>cada coluna: até {porColuna} questões</li>
			{/if}
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
				<div class="min-w-0 px-2 first:pl-0 last:pr-0 sm:px-3">
					<dt class="text-xs font-medium text-ink-soft">{m.rotulo}</dt>
					<dd
						class="nums mt-0.5 flex items-center gap-1 font-display font-extrabold {fonteMetrica} {m.xp
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

	<div class="mt-6 space-y-2.5" class:pointer-events-none={!botoesLivres} data-ato3>
		{@render extra?.()}
		{@render acoes?.(faixa)}
	</div>
</section>

<style>
	/* recebe foco só para o teclado começar no resumo; não é clicável, e o anel
	   global (fora das camadas do Tailwind) parecia um campo selecionado */
	.titulo:focus-visible {
		outline: none;
	}

	/* canto superior cortado, como as barras da marca */
	.chanfro {
		clip-path: polygon(0 min(5px, 40%), min(5px, 60%) 0, 100% 0, 100% 100%, 0 100%);
	}
</style>
