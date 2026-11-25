<script module>
	// Quatro pilares isométricos representando as 4 estações reais da trilha
	// (Estudo, Treino, Discursivas, Simulado), em diagonal ascendente.
	const PILARES = [
		{ x: 64, baseY: 162, altura: 26 },
		{ x: 126, baseY: 146, altura: 40 },
		{ x: 188, baseY: 130, altura: 54 },
		{ x: 250, baseY: 114, altura: 72 }
	];
	const RX = 25;
	const RY = 13.5;

	function faceTopo(cx, cy) {
		return `M${cx} ${cy - RY} L${cx + RX} ${cy} L${cx} ${cy + RY} L${cx - RX} ${cy} Z`;
	}
	function faceEsq(cx, topoY, baseY) {
		return `M${cx - RX} ${topoY} L${cx} ${topoY + RY} V${baseY + RY} L${cx - RX} ${baseY} Z`;
	}
	function faceDir(cx, topoY, baseY) {
		return `M${cx + RX} ${topoY} L${cx} ${topoY + RY} V${baseY + RY} L${cx + RX} ${baseY} Z`;
	}

	const FAISCAS = [
		{ dx: -26, dy: -22, cor: 'var(--milestone)' },
		{ dx: 26, dy: -20, cor: 'var(--accent-bar)' },
		{ dx: -32, dy: 4, cor: 'var(--accent)' },
		{ dx: 30, dy: 6, cor: 'var(--milestone)' },
		{ dx: 0, dy: -32, cor: 'var(--milestone)' },
		{ dx: 14, dy: -28, cor: 'var(--ok-solid)' }
	];
</script>

<script>
	import { animar, mola, reduzirMovimento } from './motion.js';

	/**
	 * Arte geométrica autoral e reativa do palco da Home.
	 * Espelha o progresso real nas 4 estações da trilha: pilares concluídos
	 * acendem em verde, a estação atual brilha no acento do curso coroada pelo
	 * prisma âmbar flutuante (mesma família da nova marca).
	 *
	 * Reage suavemente ao ponteiro (`px`, `py` em [-1, 1]) e dá um salto elástico
	 * com faíscas ao toque/clique — 100% visual, leve na GPU e estático em
	 * `prefers-reduced-motion`.
	 */
	let { etapas = [], px = 0, py = 0, compacta = false } = $props();

	let raiz = $state(null);

	let indiceCristal = $derived.by(() => {
		const atual = etapas.findIndex((e) => e.estado === 'atual');
		return atual >= 0 ? atual : Math.max(0, PILARES.length - 1);
	});

	let alvo = $derived(PILARES[indiceCristal] ?? PILARES[0]);
	let cristalY = $derived(alvo.baseY - alvo.altura - 30);

	function saltarCristal() {
		if (!raiz || reduzirMovimento()) return;
		const gema = raiz.querySelector('[data-gema-cena]');
		animar(
			gema,
			[
				{ transform: 'translateY(0px) scale(1)' },
				{ transform: 'translateY(-13px) scale(1.12, 0.92)', offset: 0.32 },
				{ transform: 'translateY(2px) scale(0.95, 1.06)', offset: 0.68 },
				{ transform: 'translateY(0px) scale(1)' }
			],
			mola(320, 15)
		);
		for (const el of raiz.querySelectorAll('[data-faisca-cena]')) {
			const f = FAISCAS[Number(el.dataset.faiscaCena)];
			if (!f) continue;
			animar(
				el,
				[
					{ opacity: 0, transform: 'translate(0px, 0px) scale(0.3)' },
					{ opacity: 1, transform: `translate(${f.dx * 0.7}px, ${f.dy * 0.7}px) scale(1.15)`, offset: 0.42 },
					{ opacity: 0, transform: `translate(${f.dx}px, ${f.dy}px) scale(0.25)` }
				],
				{ duracao: 460 }
			);
		}
	}
</script>

<div
	bind:this={raiz}
	class="cena-palco relative select-none"
	style="--px: {px}; --py: {py};"
	onpointerdown={saltarCristal}
	aria-hidden="true"
>
	<svg
		viewBox={compacta ? '22 24 274 166' : '16 14 286 196'}
		fill="none"
		class="h-auto w-full overflow-visible"
	>
		<!-- Camada de fundo: plano isométrico e anéis sutis (paralaxe leve) -->
		<g class="camada-fundo">
			<path
				d="M24 176 L158 104 L294 146 L160 212 Z"
				fill="var(--accent-soft)"
				opacity="0.55"
			/>
			<path
				d="M42 174 L268 110"
				stroke="var(--accent-border)"
				stroke-width="1.5"
				stroke-dasharray="4 6"
				opacity="0.6"
			/>
			<ellipse
				cx="256"
				cy="54"
				rx="26"
				ry="14"
				stroke="var(--milestone-border)"
				stroke-width="1.5"
				stroke-dasharray="3 5"
				opacity="0.7"
			/>
			<circle cx="52" cy="64" r="5" fill="var(--accent-soft)" stroke="var(--accent-border)" stroke-width="1.5" />
			<path
				d="M288 28 L293 33 L288 38 L283 33 Z"
				fill="var(--milestone-soft)"
				stroke="var(--milestone)"
				stroke-width="1.4"
			/>
		</g>

		<!-- Trilho de luz conectando as bases dos 4 pilares -->
		<g class="camada-media">
			{#each PILARES.slice(0, -1) as a, k (k)}
				{@const b = PILARES[k + 1]}
				{@const aceso = etapas[k]?.estado === 'feito'}
				<line
					x1={a.x}
					y1={a.baseY + 2}
					x2={b.x}
					y2={b.baseY + 2}
					stroke={aceso ? 'var(--ok-solid)' : 'var(--line-strong)'}
					stroke-width={aceso ? '4' : '2.5'}
					stroke-linecap="round"
					opacity={aceso ? '0.9' : '0.45'}
				/>
			{/each}

			<!-- Os 4 pilares isométricos -->
			{#each PILARES as p, k (k)}
				{@const estado = etapas[k]?.estado ?? (k === 0 ? 'atual' : k === 3 ? 'marco' : 'aberto')}
				{@const topoY = p.baseY - p.altura}
				{@const feito = estado === 'feito'}
				{@const atual = estado === 'atual'}
				{@const marco = estado === 'marco'}

				<!-- Sombra suave de contato -->
				<ellipse cx={p.x} cy={p.baseY + RY - 1} rx={RX + 3} ry="9" fill="#09132e" opacity="0.11" />

				{#if atual}
					<!-- Halo vivo ao redor da estação atual -->
					<ellipse
						cx={p.x}
						cy={p.baseY + 4}
						rx={RX + 11}
						ry="16"
						stroke="var(--accent)"
						stroke-width="2"
						class="pulsar-halo"
						style="transform-origin: {p.x}px {p.baseY + 4}px;"
					/>
				{/if}

				<!-- Faces esquerda, direita e topo do pilar -->
				<path
					d={faceEsq(p.x, topoY, p.baseY)}
					fill={feito
						? 'var(--ok-solid)'
						: atual
							? 'var(--accent)'
							: marco
								? 'color-mix(in oklab, var(--milestone-soft) 72%, var(--panel))'
								: 'var(--tile)'}
				/>
				<path
					d={faceDir(p.x, topoY, p.baseY)}
					fill={feito
						? 'color-mix(in oklab, var(--ok-solid) 68%, #042416)'
						: atual
							? 'color-mix(in oklab, var(--accent) 66%, #070e24)'
							: marco
								? 'color-mix(in oklab, var(--milestone-border) 55%, var(--track))'
								: 'color-mix(in oklab, var(--tile) 84%, #0b1328)'}
				/>
				<path
					d={faceTopo(p.x, topoY)}
					fill={feito
						? 'color-mix(in oklab, var(--ok-solid) 76%, white)'
						: atual
							? 'color-mix(in oklab, var(--accent-bar) 78%, white)'
							: marco
								? 'var(--milestone-soft)'
								: 'color-mix(in oklab, var(--tile) 80%, white)'}
					stroke={feito
						? 'var(--ok-solid)'
						: atual
							? 'var(--accent)'
							: marco
								? 'var(--milestone-border)'
								: 'var(--line)'}
					stroke-width="1.2"
					stroke-linejoin="round"
				/>

				{#if feito}
					<!-- Marca de conquista limpa no topo do pilar concluído -->
					<path
						d="M{p.x - 6} {topoY} L{p.x - 1.5} {topoY + 4.5} L{p.x + 7} {topoY - 4}"
						stroke="white"
						stroke-width="2.6"
						stroke-linecap="round"
						stroke-linejoin="round"
					/>
				{:else if marco && !atual}
					<!-- Losango dourado discreto no pilar da prova completa -->
					<path
						d="M{p.x} {topoY - 5} L{p.x + 6} {topoY} L{p.x} {topoY + 5} L{p.x - 6} {topoY} Z"
						fill="var(--milestone)"
					/>
				{/if}
			{/each}
		</g>

		<!-- Cristal âmbar flutuante coroando a estação ativa (reage ao ponteiro e ao toque) -->
		<g class="camada-frente">
			<g transform="translate({alvo.x} {cristalY})">
				<!-- Sombra projetada no topo do pilar ativo -->
				<ellipse cx="0" cy="29" rx="11" ry="5.5" fill="#09132e" opacity="0.22" />

				<!-- Faíscas do clique/toque (invisíveis até disparar) -->
				{#each FAISCAS as f, idx (idx)}
					<path
						data-faisca-cena={idx}
						d="M0 -4.5 L3.8 0 L0 4.5 L-3.8 0 Z"
						fill={f.cor}
						opacity="0"
					/>
				{/each}

				<g class="flutuar-cristal">
					<g data-gema-cena class="cursor-pointer">
						<path
							fill="color-mix(in oklab, var(--milestone) 64%, white)"
							d="M0 -18 L15 -10 L0 -2 L-15 -10 Z"
						/>
						<path fill="var(--milestone)" d="M-15 -10 L0 -2 V13 L-15 5 Z" />
						<path
							fill="color-mix(in oklab, var(--milestone) 72%, #3a1700)"
							d="M15 -10 L0 -2 V13 L15 5 Z"
						/>
						<!-- Filete especular nítido -->
						<path
							d="M-13.5 -9.2 L0 -2 L13.5 -9.2"
							stroke="rgba(255,255,255,0.55)"
							stroke-width="1.2"
							stroke-linecap="round"
						/>
					</g>
				</g>
			</g>
		</g>
	</svg>
</div>

<style>
	.camada-fundo,
	.camada-media,
	.camada-frente {
		transition: transform 260ms cubic-bezier(0.22, 1, 0.36, 1);
	}

	.camada-fundo {
		transform: translate3d(calc(var(--px, 0) * -4px), calc(var(--py, 0) * -3px), 0);
	}

	.camada-media {
		transform: translate3d(calc(var(--px, 0) * 3px), calc(var(--py, 0) * 2px), 0);
	}

	.camada-frente {
		transform: translate3d(calc(var(--px, 0) * 7px), calc(var(--py, 0) * 5px), 0);
	}

	@media (prefers-reduced-motion: reduce) {
		.camada-fundo,
		.camada-media,
		.camada-frente {
			transition: none !important;
			transform: none !important;
		}
	}
</style>
