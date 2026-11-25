<script module>
	// Geometria isométrica: A = profundidade de um degrau, B = largura, H = altura.
	const N = 5;
	const A = [21, -12];
	const B = [54, 31];
	const H = 17;
	const O = [26, 172];
	const ALTURA_MARCO = 25;

	function p(k, lado, z) {
		return [O[0] + A[0] * k + B[0] * lado, O[1] + A[1] * k + B[1] * lado - z * H];
	}
	function poligono(...pts) {
		return 'M' + pts.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join(' L') + ' Z';
	}

	const FUNDACAO = poligono(p(-0.9, 0, 0), p(-0.9, 1, 0), p(0, 1, 0), p(0, 0, 0));
	// de trás para a frente, para a pintura já sair na ordem certa
	const DEGRAUS = Array.from({ length: N }, (_, j) => {
		const k = N - 1 - j;
		const piso = poligono(p(k, 0, k + 1), p(k, 1, k + 1), p(k + 1, 1, k + 1), p(k + 1, 0, k + 1));
		const espelho = poligono(p(k, 0, k), p(k, 1, k), p(k, 1, k + 1), p(k, 0, k + 1));
		const lateral = poligono(p(k, 1, 0), p(k + 1, 1, 0), p(k + 1, 1, k + 1), p(k, 1, k + 1));
		return { k, piso, espelho, lateral, traco: `${espelho} ${piso} ${lateral}` };
	});

	/** Centro do piso em que o marco pousa; -1 é a fundação. */
	function chao(j) {
		return j < 0 ? p(-0.45, 0.5, 0) : p(j + 0.5, 0.5, j + 1);
	}

	// Estilhaços do pulso: losango (marco), chanfro (as barras da marca) e
	// cantoneira (o degrau). Ângulo em graus, distância em unidades do desenho.
	const FAGULHAS = [
		[-90, 52, 'losango'],
		[-58, 60, 'chanfro'],
		[-28, 50, 'cantoneira'],
		[4, 58, 'losango'],
		[40, 46, 'chanfro'],
		[78, 40, 'losango'],
		[118, 46, 'cantoneira'],
		[150, 54, 'chanfro'],
		[182, 48, 'losango'],
		[-152, 58, 'cantoneira'],
		[-122, 52, 'chanfro'],
		[-104, 66, 'losango']
	].map(([graus, dist, forma]) => {
		const r = (graus * Math.PI) / 180;
		return { dx: Math.cos(r) * dist * 1.35, dy: Math.sin(r) * dist * 1.35, giro: graus, forma };
	});
	const FORMAS = {
		losango: ['M0 -5 L4 0 L0 5 L-4 0 Z', 'var(--milestone)'],
		chanfro: ['M-7 3 L-3 -3 H7 L3 3 Z', 'var(--accent-bar)'],
		cantoneira: ['M-5 -5 H-1 V1 H5 V5 H-5 Z', 'var(--accent)']
	};

	// tempos (ms): o desenho da planta, e o marco subindo um degrau por vez
	const TRACO = 300;
	const PARTIDA = 260;
	const SALTO = 105;
</script>

<script>
	import { onMount } from 'svelte';
	import { animar, mola } from './motion.js';
	import { faixaDesempenho } from './sessao.js';

	/**
	 * Ato 1 e pulso do resumo: a escada da marca é desenhada ao vivo e o marco
	 * âmbar sobe os degraus que a sessão construiu, acendendo cada um ao pisar.
	 * Solta, sem caixa nem círculo ao redor. Quem foi mal vê a obra começada e o
	 * próximo degrau marcado, nunca um X.
	 */
	let { pct = 0, pulso = false, tempoPulso = 850, animado = true, classe = '' } = $props();

	let faixa = $derived(faixaDesempenho(pct));
	let acesos = $derived(Math.min(N, Math.max(pct > 0 ? 1 : 0, Math.floor(pct / 20 + 0.5))));
	let pouso = $derived(chao(acesos - 1));
	let fagulhas = $derived(
		faixa === 'excelente' ? FAGULHAS : faixa === 'solido' ? FAGULHAS.filter((_, k) => k % 2 === 0) : []
	);
	let aneis = $derived(faixa === 'excelente' ? [0, 140] : [0]);

	let raiz;

	/** Saltos do marco, da fundação ao degrau alcançado, relativos ao pouso. */
	function saltos() {
		const quadros = [];
		for (let j = -1; j < acesos; j++) {
			const [x, y] = chao(j);
			const dx = x - pouso[0];
			const dy = y - pouso[1];
			quadros.push({
				transform: `translate(${dx}px, ${dy}px)`,
				easing: 'cubic-bezier(0.3, 0.8, 0.5, 1)',
				offset: (j + 1) / acesos
			});
			if (j + 1 === acesos) break;
			const [x2, y2] = chao(j + 1);
			quadros.push({
				transform: `translate(${(dx + x2 - pouso[0]) / 2}px, ${Math.min(dy, y2 - pouso[1]) - 13}px)`,
				easing: 'cubic-bezier(0.5, 0, 0.8, 0.5)',
				offset: (j + 1.55) / acesos
			});
		}
		return quadros;
	}

	onMount(() => {
		if (!animado || !raiz) return;
		const um = (s) => raiz.querySelector(s);
		const todos = (s) => [...raiz.querySelectorAll(s)];
		const risco = [
			{ strokeDasharray: '1 1', strokeDashoffset: 1, opacity: 0, offset: 0 },
			{ strokeDasharray: '1 1', strokeDashoffset: 0.9, opacity: 1, offset: 0.1 },
			{ strokeDasharray: '1 1', strokeDashoffset: 0, opacity: 1, offset: 1 }
		];

		animar(um('[data-fundacao]'), risco, { duracao: TRACO });
		for (const el of todos('[data-traco]')) {
			animar(el, risco, { duracao: TRACO, atraso: 50 + el.dataset.traco * 42 });
		}
		for (const el of todos('[data-planta]')) {
			animar(el, { opacity: [0, 1] }, { duracao: 220, atraso: 160 + el.dataset.planta * 42 });
		}
		for (const el of todos('[data-aceso]')) {
			animar(
				el,
				{ opacity: [0, 1], transform: ['translateY(5px)', 'translateY(0px)'] },
				{ ...mola(380, 18), atraso: PARTIDA + (Number(el.dataset.aceso) + 1) * SALTO - 20 }
			);
		}

		const fimSubida = PARTIDA + acesos * SALTO;
		const marco = um('[data-marco]');
		if (acesos) {
			animar(marco, saltos(), { duracao: acesos * SALTO, atraso: PARTIDA, curva: 'linear' });
			animar(marco, { opacity: [0, 1] }, { duracao: 140, atraso: PARTIDA - 140 });
		} else {
			animar(
				marco,
				{ opacity: [0, 1], transform: ['translateY(-34px)', 'translateY(0px)'] },
				{ ...mola(260, 15), atraso: PARTIDA }
			);
		}
		// pousou: assenta no degrau e acende
		animar(
			um('[data-gema]'),
			{ transform: ['scale(0.72, 1.22)', 'scale(1, 1)'] },
			{ ...mola(320, 18), atraso: fimSubida }
		);
		animar(um('[data-luz]'), { opacity: [0, 1] }, { duracao: 200, atraso: fimSubida - 40 });
		animar(um('[data-sombra]'), { opacity: [0, 0.22] }, { duracao: 160, atraso: fimSubida - 40 });
		animar(um('[data-proximo]'), { opacity: [0, 1] }, { duracao: 260, atraso: fimSubida + 60 });

		if (!pulso) return;
		for (const el of todos('[data-anel]')) {
			animar(
				el,
				{ opacity: [0.95, 0], transform: ['scale(0.7)', 'scale(4.2)'] },
				{ duracao: 560, atraso: tempoPulso + Number(el.dataset.anel) }
			);
		}
		for (const el of todos('[data-fagulha]')) {
			const { dx, dy, giro } = fagulhas[el.dataset.fagulha];
			animar(
				el,
				[
					{ opacity: 0, transform: 'translate(0px, 0px) rotate(0deg) scale(0.2)' },
					{
						opacity: 1,
						transform: `translate(${dx * 0.8}px, ${dy * 0.8}px) rotate(${giro * 0.6}deg) scale(1.5)`,
						offset: 0.45
					},
					{ opacity: 0, transform: `translate(${dx}px, ${dy + 7}px) rotate(${giro}deg) scale(0.4)` }
				],
				{ duracao: 640, atraso: tempoPulso }
			);
		}
	});
</script>

<svg
	bind:this={raiz}
	viewBox="0 0 190 220"
	fill="none"
	class="overflow-visible {classe}"
	aria-hidden="true"
	stroke-linejoin="round"
	stroke-linecap="round"
>
	<path
		data-fundacao
		d={FUNDACAO}
		pathLength="1"
		fill="var(--accent-soft)"
		stroke="var(--accent-border)"
		stroke-width="1.5"
	/>

	{#each DEGRAUS as d (d.k)}
		<g data-planta={d.k}>
			<path d={d.lateral} fill="var(--track)" />
			<path d={d.espelho} fill="var(--tile)" />
			<path d={d.piso} fill="var(--panel)" />
		</g>
		{#if d.k < acesos}
			{@const topo = d.k === acesos - 1 && faixa === 'excelente'}
			<g data-aceso={d.k}>
				<path d={d.lateral} fill="color-mix(in oklab, var(--accent) 72%, black)" />
				<path d={d.espelho} fill="var(--accent)" />
				<path
					d={d.piso}
					fill={topo ? 'color-mix(in oklab, var(--milestone) 38%, white)' : 'color-mix(in oklab, var(--accent-bar) 78%, white)'}
				/>
			</g>
		{/if}
		<path
			data-traco={d.k}
			d={d.traco}
			pathLength="1"
			stroke={d.k < acesos ? 'var(--accent-ink)' : 'var(--accent-border)'}
			stroke-width="1.4"
		/>
	{/each}

	{#if faixa !== 'excelente' && acesos < N}
		{@const alvo = DEGRAUS[N - 1 - acesos]}
		<path
			data-proximo
			d="{alvo.espelho} {alvo.piso}"
			stroke="var(--milestone)"
			stroke-width="2"
			stroke-dasharray="5 5"
		/>
	{/if}

	<path
		data-sombra
		d="M{A[0] * 0.3} {A[1] * 0.3} L{B[0] * 0.16} {B[1] * 0.16} L{-A[0] * 0.3} {-A[1] * 0.3} L{-B[0] * 0.16} {-B[1] * 0.16} Z"
		transform="translate({pouso[0]} {pouso[1]})"
		fill="black"
		opacity="0.22"
	/>

	<g transform="translate({pouso[0]} {pouso[1]})">
		<g data-marco>
			<g transform="translate(0 {-ALTURA_MARCO})">
				{#if pulso}
					{#each aneis as atraso (atraso)}
						<path
							data-anel={atraso}
							d="M0 -14 L12 0 L0 14 L-12 0 Z"
							stroke="var(--milestone)"
							stroke-width="2"
							vector-effect="non-scaling-stroke"
							opacity="0"
						/>
					{/each}
					{#each fagulhas as f, k (k)}
						<path data-fagulha={k} d={FORMAS[f.forma][0]} fill={FORMAS[f.forma][1]} opacity="0" />
					{/each}
				{/if}

				<g data-gema>
					<path d="M0 -15 L13 0 L0 15 L-13 0 Z" fill="var(--card)" />
					<g data-luz>
						{#if faixa === 'construcao'}
							<path d="M-13 0 H13 L0 15 Z" fill="var(--milestone)" />
						{:else}
							<path d="M0 -15 L-13 0 L0 15 Z" fill="var(--milestone)" />
							<path d="M0 -15 L13 0 L0 15 Z" fill="color-mix(in oklab, var(--milestone) 80%, black)" />
						{/if}
						{#if faixa === 'excelente'}
							<path
								d="M0 -22 V-29 M15 -15 L20 -20 M-15 -15 L-20 -20 M20 0 H27 M-20 0 H-27"
								stroke="var(--milestone)"
								stroke-width="2.6"
							/>
						{/if}
					</g>
					<path d="M0 -15 L13 0 L0 15 L-13 0 Z" stroke="var(--milestone)" stroke-width="2" />
				</g>
			</g>
		</g>
	</g>
</svg>
