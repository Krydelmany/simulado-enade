// Remontagem de uma sessão pausada (treino ou estudo) a partir do banco.

/**
 * Remonta a fila de uma sessão salva pelos ids, tirando as questões que não
 * estão mais no banco, e REINDEXA o que é guardado por posição.
 *
 * `respostas` é um array indexado pela posição na fila, e cada registro do
 * `log` guarda essa posição em `idx`. Antes, a fila era só filtrada
 * (`.filter(Boolean)`): com uma questão a menos, tudo depois dela andava uma
 * casa — a resposta da questão 5 aparecia na 4, e o "Questão N" do retorno
 * apontava para a questão errada.
 *
 * Só chame com o banco INTEIRO: com um JSON faltando, id ausente não quer
 * dizer questão removida (ver `carregarBancoDetalhado`).
 *
 * @param {string[]} ids ordem salva da fila
 * @param {object[]} banco questões carregadas
 * @param {{respostas?: any[], log?: object[], i?: number}} salvo
 * @returns {{fila: object[], respostas: any[], log: object[], i: number, removidas: number}}
 */
export function remontarSessao(ids, banco, { respostas = [], log = [], i = 0 } = {}) {
	const mapa = new Map((Array.isArray(banco) ? banco : []).map((q) => [q.id, q]));
	const novaPos = new Map(); // posição antiga -> posição nova
	const fila = [];
	(Array.isArray(ids) ? ids : []).forEach((id, k) => {
		const q = mapa.get(id);
		if (q) {
			novaPos.set(k, fila.length);
			fila.push(q);
		}
	});

	const novasRespostas = [];
	(Array.isArray(respostas) ? respostas : []).forEach((r, k) => {
		if (r != null && novaPos.has(k)) novasRespostas[novaPos.get(k)] = r;
	});

	// registro sem `idx` é de formato antigo: fica como está
	const novoLog = (Array.isArray(log) ? log : [])
		.filter((r) => r && (r.idx == null || novaPos.has(r.idx)))
		.map((r) => (r.idx == null ? r : { ...r, idx: novaPos.get(r.idx) }));

	// a questão em que a pessoa parou pode ter saído: fica na seguinte que sobrou
	let novoI = 0;
	for (const antiga of novaPos.keys()) if (antiga < (i ?? 0)) novoI++;
	novoI = Math.max(0, Math.min(novoI, fila.length - 1));

	return {
		fila,
		respostas: novasRespostas,
		log: novoLog,
		i: novoI,
		removidas: (Array.isArray(ids) ? ids.length : 0) - fila.length
	};
}
