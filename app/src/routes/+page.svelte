<script>
	import { onMount, tick } from 'svelte';
	import { carregarBanco, contagens, ehGerada } from '$lib/banco.js';
	import { carregarSessao, getXP, getParaRevisar, historico } from '$lib/stats.js';
	import { lerProva, lerUltimo } from '$lib/simulado.js';
	import { resumoProgresso } from '$lib/resumo.js';
	import { DATA_ENADE, diasAteEnade } from '$lib/enade.js';
	import { nomeMateria } from '$lib/materias.js';
	import { cursoAtual } from '$lib/curso.js';
	import { nuvemLigada, contaLocal } from '$lib/nuvem.js';
	import { consumirConquista } from '$lib/conquista.js';
	import { animar, mola, reduzirMovimento } from '$lib/motion.js';
	import CenaHero from '$lib/CenaHero.svelte';
	import {
		ArrowRight,
		BookOpen,
		CalendarBlank,
		CaretRight,
		Check,
		Code,
		FlagCheckered,
		Infinity as InfinityIcon,
		Lightning,
		NotePencil,
		Play,
		Stairs,
		Timer,
		UsersThree
	} from 'phosphor-svelte';

	const curso = cursoAtual();
	// chave própria das discursivas (mesma de `treino/+page.svelte`)
	const CHAVE_SESSAO_DISC = 'enade-sessao-discursivas';

	let total = $state(0);
	// Apenas as discursivas do Componente Específico (as 10 que abrem em /treino/?modo=discursivas)
	let discCE = $state(0);
	let geradas = $state(0);
	let xp = $state(0);
	// `localPronto` fecha no primeiro quadro do onMount (lendo só localStorage),
	// para quem já tem sessão pausada não ver um flash de "Pronto para a primeira rodada?"
	// nem clicar no destino errado enquanto o banco JSON ainda baixa.
	let localPronto = $state(false);
	let pronto = $state(false);
	// progresso real do aluno — antes a home só mostrava XP, e XP não diz
	// nada sobre quanto a pessoa estudou
	let prog = $state(null);
	let paraRevisar = $state([]);
	// null até montar: no prerender a contagem ficaria congelada no dia do build
	let dias = $state(null);
	// Quem chega pelo link da home (e não pelo convite) estudava sem conta e
	// nunca aparecia no painel do professor. Só depois de montar: no prerender
	// não há localStorage para saber se a pessoa já entrou.
	let convidarTurma = $state(false);

	// Progresso REAL por modo (lido das sessões, histórico de ids e simulado salvo) —
	// evita dar check verde a um modo por causa de respostas feitas em outro.
	let estudoSessoes = $state(0);
	let estudoPausadoFeitas = $state(0);
	let treinoSessoes = $state(0);
	let treinoPausadoFeitas = $state(0);
	let discPausadoFeitas = $state(0);
	let discCEFeitas = $state(0);
	let ultimoSimulado = $state(null);
	let simuladoEmAndamento = $state(false);

	// sessão que acabou de terminar (bilhete do resumo): a trilha mostra o efeito
	let conquista = $state(null);
	let trilha = $state(null);

	// paralaxe suave do palco com o ponteiro (só desktop fino e sem reduced-motion)
	let px = $state(0);
	let py = $state(0);

	let temProgresso = $derived(Boolean(prog?.temDados));
	let pctAcerto = $derived(Math.round((prog?.precisaoNumero ?? 0) * 100));

	// As 3 matérias de menor acerto, só com 3+ respostas: com 1 ou 2 o
	// percentual é sorte, e a lista mandaria o aluno estudar a coisa errada.
	let reforcar = $derived(
		(prog?.porMateria ?? [])
			.filter((m) => m.nome && m.acertosNumero + m.errosNumero >= 3)
			.sort((a, b) => a.precisaoNumero - b.precisaoNumero)
			.slice(0, 3)
	);

	// "29 de novembro", sem depender do fuso do servidor do build
	const DATA_EXTENSO = (() => {
		const [, m, d] = DATA_ENADE.split('-').map(Number);
		const MESES = [
			'janeiro',
			'fevereiro',
			'março',
			'abril',
			'maio',
			'junho',
			'julho',
			'agosto',
			'setembro',
			'outubro',
			'novembro',
			'dezembro'
		];
		return `${d} de ${MESES[m - 1]}`;
	})();

	function lerSessaoEstudoFeitas() {
		try {
			const bruto = localStorage.getItem('enade-sessao-estudo');
			if (!bruto) return 0;
			const s = JSON.parse(bruto);
			return Array.isArray(s?.log) ? s.log.filter((r) => !r.pulada).length : 0;
		} catch {
			return 0;
		}
	}

	function contarFeitasSessao(s, modoEsperado) {
		return s && (s.modo ?? 'treino') === modoEsperado && Array.isArray(s.log)
			? s.log.filter((r) => !r.pulada).length
			: 0;
	}

	// Trilha viva mapeada nos dados reais de cada modo:
	//  - `feito` só quando o próprio modo teve conclusão real;
	//  - exatamente um nó `atual` (o primeiro ainda não concluído).
	let etapasTrilha = $derived.by(() => {
		const estudoFeito = estudoSessoes > 0;
		const treinoFeito = treinoSessoes > 0;
		const discFeito = discCE > 0 && discCEFeitas >= discCE;
		const simuladoFeito = Boolean(ultimoSimulado);

		const feitos = [estudoFeito, treinoFeito, discFeito, simuladoFeito];
		const ativoIdx = feitos.findIndex((f) => !f);

		const estadoDe = (idx, feito, padrao = 'aberto') =>
			feito ? 'feito' : idx === ativoIdx ? 'atual' : padrao;

		return [
			{
				passo: '01',
				href: '/estudo/',
				icone: Stairs,
				titulo: 'Estudo por níveis',
				tituloCurto: 'estudo por níveis',
				desc: '10 questões rápidas por nível ou matéria.',
				selo: estudoFeito
					? `${estudoSessoes} ${estudoSessoes === 1 ? 'sessão' : 'sessões'}`
					: estudoPausadoFeitas > 0
						? `${estudoPausadoFeitas} em aberto`
						: '10 por rodada',
				cta: estudoPausadoFeitas > 0 ? 'Retomar' : 'Começar',
				estado: estadoDe(0, estudoFeito),
				emAndamento: !estudoFeito && estudoPausadoFeitas > 0
			},
			{
				passo: '02',
				href: '/treino/',
				icone: InfinityIcon,
				titulo: 'Treino livre',
				tituloCurto: 'treino livre',
				desc: 'Fila contínua com correção e resolução na hora.',
				selo: treinoFeito
					? `${treinoSessoes} ${treinoSessoes === 1 ? 'sessão' : 'sessões'}`
					: treinoPausadoFeitas > 0
						? `${treinoPausadoFeitas} em aberto`
						: total + geradas
							? `${total + geradas} questões`
							: 'Banco inteiro',
				cta: treinoPausadoFeitas > 0 ? 'Continuar' : 'Praticar',
				estado: estadoDe(1, treinoFeito),
				emAndamento: !treinoFeito && treinoPausadoFeitas > 0
			},
			{
				passo: '03',
				href: '/treino/?modo=discursivas',
				icone: NotePencil,
				titulo: 'Discursivas do CE',
				tituloCurto: 'discursivas',
				desc: 'Treine a escrita com o padrão oficial do INEP.',
				selo:
					discPausadoFeitas > 0 && !discFeito
						? `${discPausadoFeitas} em aberto`
						: discCEFeitas > 0 && discCE > 0
							? `${discCEFeitas}/${discCE} ${discCEFeitas === 1 ? 'feita' : 'feitas'}`
							: discCE
								? `${discCE} oficiais`
								: 'Padrão INEP',
				cta: discPausadoFeitas > 0 ? 'Retomar' : discCEFeitas > 0 ? 'Continuar' : 'Escrever',
				estado: estadoDe(2, discFeito),
				emAndamento: !discFeito && (discPausadoFeitas > 0 || discCEFeitas > 0)
			},
			{
				passo: '04',
				href: '/simulado/',
				icone: Timer,
				titulo: 'Simulado ENADE 2026',
				tituloCurto: 'simulado completo',
				desc: '15 FG · 30 CE · 1 discursiva em 4 horas.',
				selo: ultimoSimulado
					? `${ultimoSimulado.certas}/${ultimoSimulado.total} (${Math.round((ultimoSimulado.certas / ultimoSimulado.total) * 100)}%)`
					: simuladoEmAndamento
						? 'Em andamento'
						: '46 questões · 4 h',
				cta: simuladoEmAndamento ? 'Continuar' : ultimoSimulado ? 'Refazer' : 'Abrir',
				estado: estadoDe(3, simuladoFeito, 'marco'),
				emAndamento: !simuladoFeito && simuladoEmAndamento
			}
		];
	});

	let etapasFeitas = $derived(etapasTrilha.filter((e) => e.estado === 'feito').length);
	let proximaEtapa = $derived(etapasTrilha.find((e) => e.estado === 'atual') ?? null);

	// O palco sempre abre apontando direto para o próximo passo real do aluno.
	let acaoPrincipal = $derived.by(() => {
		if (simuladoEmAndamento) {
			return {
				href: '/simulado/',
				titulo: 'Seu simulado está esperando.',
				sub: 'O cronômetro continua pausado até você voltar para a prova.',
				botao: 'Continuar simulado',
				play: true
			};
		}
		if (estudoPausadoFeitas > 0) {
			return {
				href: '/estudo/',
				titulo: 'Volte de onde você parou.',
				sub: `${estudoPausadoFeitas} ${estudoPausadoFeitas === 1 ? 'questão respondida' : 'questões respondidas'} na sua sessão de estudo.`,
				botao: 'Retomar estudo',
				play: true
			};
		}
		if (treinoPausadoFeitas > 0) {
			return {
				href: '/treino/',
				titulo: 'Continue no seu ritmo.',
				sub: `${treinoPausadoFeitas} ${treinoPausadoFeitas === 1 ? 'questão feita' : 'questões feitas'} na fila de treino atual.`,
				botao: 'Retomar treino',
				play: true
			};
		}
		if (discPausadoFeitas > 0) {
			return {
				href: '/treino/?modo=discursivas',
				titulo: 'Volte para suas discursivas.',
				sub: `${discPausadoFeitas} ${discPausadoFeitas === 1 ? 'discursiva praticada' : 'discursivas praticadas'} na sessão em aberto.`,
				botao: 'Retomar discursivas',
				play: true
			};
		}
		if (temProgresso && proximaEtapa) {
			const nResp = prog.respondidasNumero;
			return {
				href: proximaEtapa.href,
				titulo: `Hora de avançar em ${proximaEtapa.tituloCurto}.`,
				sub: `${nResp} ${nResp === 1 ? 'respondida' : 'respondidas'} · ${pctAcerto}% de acerto${prog.ultimoTreinoRelativo ? ` · último estudo ${prog.ultimoTreinoRelativo}` : ''}.`,
				botao: `${proximaEtapa.cta} agora`,
				play: false
			};
		}
		if (temProgresso) {
			const nResp = prog.respondidasNumero;
			return {
				href: '/treino/',
				titulo: 'Trilha completa. Mantenha o ritmo.',
				sub: `${nResp} ${nResp === 1 ? 'respondida' : 'respondidas'} · ${pctAcerto}% de acerto geral.`,
				botao: 'Treinar agora',
				play: true
			};
		}
		return {
			href: '/estudo/',
			titulo: 'Pronto para a primeira rodada?',
			sub: '10 questões rápidas para aquecer, com resolução na hora.',
			botao: 'Começar agora',
			play: true
		};
	});

	let acaoSecundaria = $derived(
		acaoPrincipal.href === '/simulado/'
			? { href: '/treino/', rotulo: 'Treino livre' }
			: { href: '/simulado/', rotulo: 'Simulado real' }
	);

	function paralaxePalco(el) {
		const aoMover = (e) => {
			if (e.pointerType !== 'mouse' || reduzirMovimento()) return;
			const r = el.getBoundingClientRect();
			if (!r.width || !r.height) return;
			px = Math.max(-1, Math.min(1, ((e.clientX - r.left) / r.width) * 2 - 1));
			py = Math.max(-1, Math.min(1, ((e.clientY - r.top) / r.height) * 2 - 1));
		};
		const aoSair = () => {
			px = 0;
			py = 0;
		};
		el.addEventListener('pointermove', aoMover, { passive: true });
		el.addEventListener('pointerleave', aoSair, { passive: true });
		return () => {
			el.removeEventListener('pointermove', aoMover);
			el.removeEventListener('pointerleave', aoSair);
		};
	}

	onMount(async () => {
		// Lê tudo que já mora no aparelho ANTES de esperar a rede do banco,
		// evitando flash do texto de primeira visita para quem tem sessão pausada.
		dias = diasAteEnade();
		convidarTurma = nuvemLigada && !contaLocal();
		xp = getXP();
		prog = resumoProgresso();

		const hist = historico();
		estudoSessoes = hist.sessoes.filter((s) => s.modo === 'estudo' && s.respondidas > 0).length;
		treinoSessoes = hist.sessoes.filter((s) => s.modo === 'treino' && s.respondidas > 0).length;
		estudoPausadoFeitas = lerSessaoEstudoFeitas();
		treinoPausadoFeitas = contarFeitasSessao(carregarSessao(), 'treino');
		discPausadoFeitas = contarFeitasSessao(carregarSessao(CHAVE_SESSAO_DISC), 'discursivas');
		ultimoSimulado = lerUltimo();
		const provaSalva = lerProva();
		simuladoEmAndamento = Boolean(provaSalva && !provaSalva.entregue);
		localPronto = true;

		try {
			const b = await carregarBanco();
			// `contagens` é a mesma função que o resto do app usa, então a home
			// não pode mais divergir do que o treino está mostrando
			const c = contagens(b);
			total = c.total;
			const idsDiscCE = new Set(
				b.filter((q) => !ehGerada(q) && q.parte === 'CE' && q.tipo === 'discursiva').map((q) => q.id)
			);
			discCE = idsDiscCE.size;
			geradas = c.geradas;
			discCEFeitas = hist.questoes.filter((q) => idsDiscCE.has(q.id) && q.respostas > 0).length;

			// só o que ainda está no banco: uma questão que saiu (as anuladas)
			// continuava contada aqui, e a revisão abria com menos do que o botão
			// prometia
			const ids = new Set(b.map((q) => q.id));
			paraRevisar = getParaRevisar().filter((id) => ids.has(id));
		} finally {
			// sempre fecha o esqueleto — sem "loading eterno" nem tela em branco
			pronto = true;
		}
		// quem já saiu da home enquanto o banco carregava não gasta o bilhete
		if (!trilha) return;
		conquista = consumirConquista();
		if (!conquista) return;
		await tick();
		celebrarNaTrilha();
	});

	/**
	 * Causa e efeito na trilha: o nó concluído acende, a linha desce dele até o
	 * próximo passo, e o próximo passo acorda.
	 */
	function celebrarNaTrilha() {
		const feito = trilha?.querySelector('[data-agora]');
		if (!feito) return;
		const r = feito.getBoundingClientRect();
		const fora = r.top < 72 || r.bottom > window.innerHeight - 16;
		// a trilha fica abaixo da dobra no celular: sem levar até ela, o efeito
		// acontecia onde ninguém via. Uma vez por sessão concluída.
		if (fora) {
			feito.scrollIntoView({ block: 'center', behavior: reduzirMovimento() ? 'auto' : 'smooth' });
		}
		const t0 = fora ? 520 : 160;
		const um = (li, sel) => li?.querySelector(sel);
		const acender = (li, atraso) => {
			animar(um(li, '[data-no]'), { transform: ['scale(0.45)', 'scale(1)'] }, { ...mola(260, 13), atraso });
			animar(
				um(li, '[data-onda]'),
				{ opacity: [0.9, 0], transform: ['scale(1)', 'scale(2.1)'] },
				{ duracao: 620, atraso: atraso + 60 }
			);
			animar(
				um(li, '[data-aviso]'),
				{ opacity: [0, 1], transform: ['translateX(-8px) scale(0.85)', 'translateX(0px) scale(1)'] },
				{ ...mola(300, 16), atraso: atraso + 120 }
			);
		};
		acender(feito, t0);
		animar(um(feito, '[data-trecho]'), { transform: ['scaleY(0)', 'scaleY(1)'] }, { duracao: 420, atraso: t0 + 320 });

		animar(
			um(feito, '[data-atalho]'),
			{ opacity: [0, 1], transform: ['translateY(8px)', 'translateY(0px)'] },
			{ duracao: 260, atraso: t0 + 620 }
		);
		const proximo = trilha.querySelector('[data-proximo]');
		if (!proximo || proximo === feito) return;
		acender(proximo, t0 + 700);
		animar(
			um(proximo, '[data-brilho]'),
			[{ opacity: 0 }, { opacity: 1, offset: 0.25 }, { opacity: 0 }],
			{ duracao: 900, atraso: t0 + 760 }
		);
	}
</script>

<!-- 1. Palco vivo: próximo passo pronto para clicar + arte geométrica reativa + progresso real -->
<section
	class="palco-vivo rise overflow-clip rounded-[2rem] p-5 sm:p-7 lg:p-9"
	{@attach paralaxePalco}
>
	<div class="grid gap-6 lg:grid-cols-[1.18fr_0.82fr] lg:items-center lg:gap-8">
		<div>
			<div class="flex flex-wrap items-center gap-2">
				<p
					class="inline-flex min-h-8 items-center gap-1.5 rounded-full border border-milestone-border bg-milestone-soft px-3 py-1 text-xs font-extrabold text-milestone-ink"
				>
					<CalendarBlank size={14} weight="bold" aria-hidden="true" />
					{#if dias !== null && dias > 1}
						<span>Faltam <span class="nums">{dias} dias</span> · ENADE</span>
					{:else if dias === 1}
						<span>ENADE é amanhã</span>
					{:else if dias === 0}
						<span>ENADE é hoje. Boa prova!</span>
					{:else}
						<span>ENADE · {DATA_EXTENSO}</span>
					{/if}
				</p>
				{#if xp > 0}
					<span
						class="nums inline-flex min-h-8 items-center gap-1 rounded-full border border-milestone-border/80 bg-card/90 px-3 py-1 text-xs font-extrabold text-milestone-ink"
					>
						<Lightning size={14} weight="fill" class="text-milestone" aria-hidden="true" />
						{xp} XP
					</span>
				{:else}
					<span class="rounded-full bg-panel px-3 py-1 text-xs font-bold text-ink-soft">
						{curso.nome}
					</span>
				{/if}
			</div>

			{#if !localPronto}
				<h1 class="sr-only">Simulado ENADE — {curso.nome}</h1>
				<div class="mt-4 space-y-3" role="status" aria-label="Carregando seu próximo passo">
					<div class="h-11 w-4/5 animate-pulse rounded-2xl bg-skel"></div>
					<div class="h-5 w-3/5 animate-pulse rounded-xl bg-skel"></div>
					<div class="mt-6 flex flex-col gap-3 sm:flex-row">
						<div class="h-13 w-full animate-pulse rounded-2xl bg-skel sm:w-48"></div>
						<div class="h-13 w-full animate-pulse rounded-2xl bg-skel sm:w-40"></div>
					</div>
				</div>
			{:else}
				<h1 class="mt-4 font-display text-hero font-extrabold text-balance text-ink">
					{acaoPrincipal.titulo}
				</h1>

				<p class="mt-2.5 max-w-[42ch] text-[15px] leading-relaxed text-pretty text-ink-soft sm:text-base">
					{acaoPrincipal.sub}
				</p>

				<div class="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
					<a
						href={acaoPrincipal.href}
						class="btn-primario group/cta inline-flex min-h-13 items-center justify-center gap-2 rounded-2xl px-7 font-display text-base font-extrabold"
					>
						{#if acaoPrincipal.play}
							<Play size={18} weight="fill" aria-hidden="true" />
						{/if}
						{acaoPrincipal.botao}
						{#if !acaoPrincipal.play}
							<ArrowRight
								size={18}
								weight="bold"
								class="transition-transform duration-150 group-hover/cta:translate-x-0.5"
								aria-hidden="true"
							/>
						{/if}
					</a>
					<a
						href={acaoSecundaria.href}
						class="btn-suave inline-flex min-h-13 items-center justify-center gap-2 rounded-2xl px-6 font-display text-[15px] font-bold"
					>
						{acaoSecundaria.rotulo}
					</a>
				</div>
			{/if}

			<!-- Faixa viva de progresso dentro do palco (sem caixa institucional separada) -->
			<div class="mt-6 border-t border-line/80 pt-4">
				{#if !pronto}
					<div class="flex items-center gap-3" role="status" aria-label="Carregando progresso">
						<div class="h-3 w-32 animate-pulse rounded-full bg-skel"></div>
						<div class="h-3 w-20 animate-pulse rounded-full bg-skel"></div>
					</div>
				{:else if total === 0}
					<p
						class="rounded-2xl border border-dashed border-warn-line bg-warn-bg px-3.5 py-2.5 text-sm font-semibold text-warn-fg"
						role="alert"
					>
						As questões não carregaram.
						<button type="button" class="font-extrabold underline" onclick={() => location.reload()}>
							Recarregar agora
						</button>
					</p>
				{:else if temProgresso}
					<div class="flex flex-wrap items-center gap-x-5 gap-y-2.5">
						<div class="flex items-center gap-2">
							<div class="flex gap-1" aria-hidden="true">
								{#each etapasTrilha as e (e.href)}
									<span
										class="h-2.5 w-6 rounded-full transition-colors {e.estado === 'feito'
											? 'bg-ok-solid'
											: e.estado === 'atual'
												? 'bg-accent'
												: 'bg-track'}"
									></span>
								{/each}
							</div>
							<span class="nums text-xs font-extrabold text-ink">{etapasFeitas}/4 etapas</span>
						</div>

						<div class="flex flex-wrap items-center gap-3 text-xs font-bold text-ink-soft">
							<span class="nums">
								<strong class="text-ink">{prog.respondidasNumero}</strong>
								{prog.respondidasNumero === 1 ? 'feita' : 'feitas'}
							</span>
							<span class="nums {pctAcerto >= 50 ? 'text-ok-fg' : 'text-ink-soft'}">
								<strong class={pctAcerto >= 50 ? '' : 'text-ink'}>{pctAcerto}%</strong> acerto
							</span>
							{#if paraRevisar.length}
								<a
									href="/treino/?modo=revisao"
									class="nums inline-flex min-h-11 items-center gap-1.5 rounded-full bg-accent-soft px-4 py-2 font-extrabold text-accent-ink transition-colors hover:bg-accent hover:text-accent-on"
								>
									Revisar {paraRevisar.length}
									<ArrowRight size={14} weight="bold" aria-hidden="true" />
								</a>
							{/if}
						</div>
					</div>
				{:else}
					<div class="flex flex-wrap items-center justify-between gap-2">
						<div class="flex items-center gap-2">
							<div class="flex gap-1" aria-hidden="true">
								{#each etapasTrilha as e (e.href)}
									<span
										class="h-2.5 w-6 rounded-full {e.estado === 'atual' ? 'bg-accent' : 'bg-track'}"
									></span>
								{/each}
							</div>
							<span class="nums text-xs font-bold text-ink-soft">0 de 4 etapas</span>
						</div>
						<p class="nums text-xs font-semibold text-ink-soft">
							{total} oficiais do INEP{#if geradas}{' · '}{geradas} guiadas{/if}
						</p>
					</div>
				{/if}
			</div>
		</div>

		<!-- Arte geométrica autoral (lado direito no desktop; compacta e leve no celular) -->
		<div class="mx-auto w-full max-w-[270px] sm:max-w-[310px] lg:max-w-none">
			<div class="lg:hidden">
				<CenaHero etapas={etapasTrilha} {px} {py} compacta />
			</div>
			<div class="hidden lg:block">
				<CenaHero etapas={etapasTrilha} {px} {py} />
			</div>
		</div>
	</div>
</section>

{#if convidarTurma}
	<a
		href="/conta/"
		class="cartao-tatil rise group mt-4 flex min-h-14 items-center gap-3 rounded-2xl border-accent-border/80 px-4 py-3"
	>
		<UsersThree size={22} weight="bold" class="shrink-0 text-accent-ink" aria-hidden="true" />
		<span class="min-w-0 flex-1 text-sm font-bold text-ink">
			Tem código da turma? <span class="font-medium text-ink-soft">Entre para sincronizar e ver o ranking.</span>
		</span>
		<CaretRight
			size={18}
			weight="bold"
			class="shrink-0 text-accent-ink transition-transform group-hover:translate-x-0.5"
			aria-hidden="true"
		/>
	</a>
{/if}

<!-- 2. Trilha em estações táteis + Reforçar & Da turma ao lado no desktop -->
<div class="mt-9 grid gap-8 lg:mt-11 lg:grid-cols-[1.45fr_0.95fr] lg:items-start">
	<section id="trilha" bind:this={trilha} class="scroll-mt-20" aria-labelledby="titulo-trilha">
		<div class="flex items-center justify-between gap-3">
			<h2 id="titulo-trilha" class="font-display text-title font-extrabold text-ink">Sua trilha</h2>
			<span class="nums rounded-full bg-panel px-3 py-1 text-xs font-extrabold text-ink-soft">
				{etapasFeitas} de 4 {etapasFeitas === 1 ? 'concluída' : 'concluídas'}
			</span>
		</div>

		<p class="sr-only" role="status">
			{#if conquista}
				Sessão registrada na trilha: {conquista.certas} de {conquista.total} acertos.
				{#if proximaEtapa}Próximo passo: {proximaEtapa.titulo}.{/if}
			{/if}
		</p>

		<nav class="relative mt-4" aria-label="Trilha de estudo">
			<!-- Trilho estrutural mais encorpado ligando as estações -->
			<div
				class="pointer-events-none absolute top-7 bottom-7 left-[21px] w-1 rounded-full bg-track"
				aria-hidden="true"
			></div>

			<ol class="space-y-3.5">
				{#each etapasTrilha as etapa, k (etapa.href)}
					{@const agora = conquista?.etapa === etapa.href}
					{@const atual = etapa.estado === 'atual'}
					<li
						class="rise relative pl-14 sm:pl-16"
						style="animation-delay: {k * 45}ms"
						data-agora={agora ? '' : undefined}
						data-proximo={atual ? '' : undefined}
					>
						{#if etapa.estado === 'feito' && k < etapasTrilha.length - 1}
							<!-- trecho já percorrido, do nó concluído ao seguinte -->
							<span
								data-trecho
								aria-hidden="true"
								class="pointer-events-none absolute top-14 -bottom-9 left-[21px] w-1 origin-top rounded-full bg-ok-solid"
							></span>
						{/if}

						<!-- Nó tátil da estação -->
						<span
							data-no
							aria-hidden="true"
							class="absolute top-4 left-0 flex h-11 w-11 items-center justify-center rounded-2xl border-2 transition-transform {etapa.estado ===
							'feito'
								? 'border-ok-solid bg-ok-solid text-white shadow-[0_3px_0_0_color-mix(in_oklab,var(--ok-solid)_60%,#042416)]'
								: atual
									? 'border-accent bg-accent text-accent-on ring-4 ring-accent-soft shadow-[0_3px_0_0_var(--accent-lip)]'
									: etapa.estado === 'marco'
										? 'border-milestone-border bg-milestone-soft text-milestone-ink shadow-[0_3px_0_0_var(--milestone-border)]'
										: 'border-line-strong/60 bg-card text-ink-soft shadow-[0_2.5px_0_0_var(--surface-lip)]'}"
						>
							{#if etapa.estado === 'feito'}
								<Check size={20} weight="bold" />
							{:else if etapa.estado === 'marco'}
								<FlagCheckered size={20} weight="bold" />
							{:else}
								<etapa.icone size={20} weight="bold" />
							{/if}
							<span
								data-onda
								class="absolute -inset-1 rounded-2xl border-2 opacity-0 {etapa.estado === 'feito'
									? 'border-ok-solid'
									: 'border-accent'}"
							></span>
						</span>

						<a
							href={etapa.href}
							class="cartao-tatil group relative block rounded-3xl p-4 sm:p-5 {atual
								? 'cartao-tatil-ativo'
								: ''}"
						>
							<span
								data-brilho
								aria-hidden="true"
								class="pointer-events-none absolute -inset-px rounded-3xl border-2 border-accent opacity-0"
							></span>

							<div class="flex items-center justify-between gap-3">
								<div class="min-w-0 flex-1">
									<div class="flex flex-wrap items-center gap-2">
										{#if agora}
											<!-- discursivas: a etapa só fecha com as 10, então uma sessão dela é prática -->
											<span
												data-aviso
												class="nums rounded-full bg-ok-solid px-2.5 py-0.5 text-xs font-extrabold text-white"
											>
												{etapa.estado === 'feito' ? 'Concluído' : 'Feito'} agora · {conquista.certas}/{conquista.total}
											</span>
										{:else if etapa.estado === 'feito'}
											<span class="rounded-full bg-ok-bg px-2.5 py-0.5 text-xs font-extrabold text-ok-fg">
												Concluído
											</span>
										{:else if etapa.emAndamento}
											<span class="rounded-full bg-accent-soft px-2.5 py-0.5 text-xs font-extrabold text-accent-ink">
												Em andamento
											</span>
										{:else if atual}
											<span
												data-aviso
												class="rounded-full bg-accent-soft px-2.5 py-0.5 text-xs font-extrabold text-accent-ink"
											>
												Próximo passo
											</span>
										{:else if etapa.estado === 'marco'}
											<span
												class="rounded-full bg-milestone-soft px-2.5 py-0.5 text-xs font-extrabold text-milestone-ink"
											>
												Prova completa
											</span>
										{/if}
										{#if !agora}
											<span class="nums text-xs font-bold text-ink-soft">{etapa.selo}</span>
										{/if}
									</div>

									<h3 class="mt-2 font-display text-heading font-extrabold text-ink group-hover:text-accent-ink">
										{etapa.titulo}
									</h3>
									<p class="mt-0.5 text-sm leading-snug text-pretty text-ink-soft">
										{etapa.desc}
									</p>
								</div>

								<span
									class="hidden shrink-0 items-center gap-1 rounded-xl px-3.5 py-2 font-display text-xs font-extrabold transition-colors sm:inline-flex {atual
										? 'bg-accent text-accent-on shadow-[0_2px_0_0_var(--accent-lip)]'
										: 'bg-panel text-ink group-hover:bg-accent-soft group-hover:text-accent-ink'}"
								>
									{etapa.cta}
									<CaretRight size={14} weight="bold" aria-hidden="true" />
								</span>
								<CaretRight
									size={20}
									weight="bold"
									class="shrink-0 text-ink-soft transition-transform group-hover:translate-x-0.5 group-hover:text-accent-ink sm:hidden"
									aria-hidden="true"
								/>
							</div>
						</a>

						{#if agora && proximaEtapa && proximaEtapa !== etapa && proximaEtapa !== etapasTrilha[k + 1]}
							<!-- quem foi direto ao simulado tem o próximo passo lá em cima, fora da tela -->
							<a
								data-atalho
								href={proximaEtapa.href}
								class="mt-1 inline-flex min-h-11 items-center gap-1.5 px-1 text-sm font-bold text-accent-ink"
							>
								Próximo passo: {proximaEtapa.titulo}
								<ArrowRight size={15} weight="bold" aria-hidden="true" />
							</a>
						{/if}
					</li>
				{/each}
			</ol>
		</nav>
	</section>

	<!-- Coluna lateral (desktop) / bloco leve abaixo (celular): Reforçar + Da turma -->
	<aside class="space-y-7">
		{#if reforcar.length}
			<section aria-labelledby="titulo-reforcar">
				<h2 id="titulo-reforcar" class="font-display text-heading font-extrabold text-ink">
					Onde reforçar
				</h2>
				<ul class="mt-3 space-y-2.5">
					{#each reforcar as m (m.nome)}
						<li>
							<a
								href="/treino/?materia={m.nome}"
								class="cartao-tatil group block rounded-2xl px-4 py-3.5"
							>
								<div class="flex items-baseline justify-between gap-3 text-sm">
									<span class="min-w-0 truncate font-bold text-ink group-hover:text-accent-ink">
										{nomeMateria(m.nome)}
									</span>
									<span class="nums shrink-0 text-xs font-extrabold text-ink-soft">{m.precisao}</span>
								</div>
								<div class="mt-2 h-2 overflow-hidden rounded-full bg-track" aria-hidden="true">
									<div
										class="h-full rounded-full bg-accent-bar transition-[width] duration-300"
										style="width: {Math.round(m.precisaoNumero * 100)}%"
									></div>
								</div>
							</a>
						</li>
					{/each}
				</ul>
			</section>
		{/if}

		<section aria-labelledby="titulo-turma-materiais">
			<div class="flex items-center justify-between gap-2">
				<h2 id="titulo-turma-materiais" class="font-display text-heading font-extrabold text-ink">
					Da turma
				</h2>
				<span class="rounded-full bg-milestone-soft px-2.5 py-0.5 text-xs font-extrabold text-milestone-ink">
					Extras
				</span>
			</div>

			<div class="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
				<a href="/poo/" class="cartao-tatil group flex flex-col justify-between rounded-3xl p-4 sm:p-5">
					<div>
						<div class="flex items-center justify-between gap-2">
							<span class="inline-flex items-center gap-2 font-display text-base font-extrabold text-ink group-hover:text-accent-ink">
								<Code size={20} weight="bold" class="shrink-0 text-accent-ink" aria-hidden="true" />
								Questionário de POO
							</span>
							<span class="nums shrink-0 rounded-full bg-panel px-2.5 py-0.5 text-xs font-bold text-ink-soft">
								28/10
							</span>
						</div>
						<p class="mt-1.5 text-sm leading-snug text-ink-soft">
							10 questões do professor com correção no fim.
						</p>
					</div>
					<span class="mt-3.5 inline-flex items-center gap-1.5 text-xs font-extrabold text-accent-ink">
						Abrir questionário
						<ArrowRight
							size={14}
							weight="bold"
							class="transition-transform group-hover:translate-x-0.5"
							aria-hidden="true"
						/>
					</span>
				</a>

				<a href="/guia/" class="cartao-tatil group flex flex-col justify-between rounded-3xl p-4 sm:p-5">
					<div>
						<div class="flex items-center justify-between gap-2">
							<span class="inline-flex items-center gap-2 font-display text-base font-extrabold text-ink group-hover:text-accent-ink">
								<BookOpen size={20} weight="bold" class="shrink-0 text-accent-ink" aria-hidden="true" />
								Guia do Matheus
							</span>
							<span class="nums shrink-0 rounded-full bg-panel px-2.5 py-0.5 text-xs font-bold text-ink-soft">
								25/11
							</span>
						</div>
						<p class="mt-1.5 text-sm leading-snug text-ink-soft">
							Resumos, fórmulas e 26 questões comentadas.
						</p>
					</div>
					<span class="mt-3.5 inline-flex items-center gap-1.5 text-xs font-extrabold text-accent-ink">
						Explorar guia
						<ArrowRight
							size={14}
							weight="bold"
							class="transition-transform group-hover:translate-x-0.5"
							aria-hidden="true"
						/>
					</span>
				</a>
			</div>
		</section>
	</aside>
</div>
