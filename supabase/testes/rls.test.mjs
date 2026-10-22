// Testa a migração com um Postgres de verdade (PGlite, WASM) — sem Docker e
// sem projeto no Supabase. O schema `auth` é um dublê mínimo do Supabase:
// `auth.users` + `auth.uid()` lendo o claim `sub`, e os papéis anon/authenticated.
//
//   cd supabase/testes && npm install && npm test
//
// Cada `como(usuario, sql)` roda como `authenticated` com aquele `sub`, então a
// RLS e os grants valem de verdade (superusuário passaria por cima de tudo).

import { PGlite } from '@electric-sql/pglite';
import { readFileSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const aqui = dirname(fileURLToPath(import.meta.url));
const pastaMigracoes = join(aqui, '..', 'migrations');

const DUBLE_AUTH = `
	create role anon nologin;
	create role authenticated nologin;
	create schema auth;
	grant usage on schema auth to anon, authenticated;
	create table auth.users (id uuid primary key, raw_user_meta_data jsonb not null default '{}');
	create function auth.uid() returns uuid language sql stable as
		$$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
	grant execute on function auth.uid() to anon, authenticated;
	grant usage on schema public to anon, authenticated;
`;

const db = new PGlite();
await db.exec(DUBLE_AUTH);
for (const f of readdirSync(pastaMigracoes).filter((f) => f.endsWith('.sql')).sort()) {
	await db.exec(readFileSync(join(pastaMigracoes, f), 'utf8'));
}

const U = {
	prof: '00000000-0000-0000-0000-00000000000a',
	ana: '00000000-0000-0000-0000-00000000000b',
	beto: '00000000-0000-0000-0000-00000000000c',
	intruso: '00000000-0000-0000-0000-00000000000d'
};

async function como(usuario, sql, params = []) {
	await db.exec('reset role');
	await db.query(`select set_config('request.jwt.claim.sub', $1, false)`, [usuario ?? '']);
	await db.exec(usuario ? 'set role authenticated' : 'set role anon');
	try {
		return (await db.query(sql, params)).rows;
	} finally {
		await db.exec('reset role');
	}
}

async function falha(promessa, trecho) {
	await assert.rejects(promessa, (e) => {
		assert.match(String(e.message), trecho);
		return true;
	});
}

let n = 0;
async function teste(nome, fn) {
	await fn();
	n++;
	console.log('ok', nome);
}

// --- preparo (como admin, igual ao painel do Supabase) ---------------------
for (const [k, id] of Object.entries(U)) {
	await db.query(`insert into auth.users (id, raw_user_meta_data) values ($1, $2)`, [
		id,
		JSON.stringify({ full_name: `Nome ${k}` })
	]);
}
const [turma] = (
	await db.query(
		`insert into public.turmas (curso, instituicao, nome, data_prova, codigo)
		 values ('engcomp', 'Unisalesiano', 'Eng. Comp. 2026', '2026-11-29', 'ENGC26') returning id`
	)
).rows;
await db.query(
	`insert into public.membros (turma_id, usuario_id, papel, apelido) values ($1, $2, 'professor', 'Prof')`,
	[turma.id, U.prof]
);

const resp = (usuario, questao, resultado, extra = {}) =>
	como(
		usuario,
		`insert into public.respostas (id, questao_id, oficial, parte, materia, modo, resultado, duracao_ms, respondida_em)
		 values (gen_random_uuid(), $1, $2, $3, $4, $5, $6, 1000, coalesce($7::timestamptz, now())) returning usuario_id`,
		[questao, extra.oficial ?? true, extra.parte ?? 'CE', extra.materia ?? 'algoritmos', extra.modo ?? 'treino', resultado, extra.em ?? null]
	);

// --- testes ------------------------------------------------------------------
await teste('perfil nasce do login com o nome do Google', async () => {
	const r = await como(U.ana, 'select nome from public.perfis');
	assert.deepEqual(r, [{ nome: 'Nome ana' }]);
});

await teste('cada um muda só o próprio nome (e só o nome)', async () => {
	await como(U.ana, `update public.perfis set nome = 'Ana Souza' where id = $1`, [U.ana]);
	await como(U.ana, `update public.perfis set nome = 'Hackeado' where id = $1`, [U.beto]);
	const r = (await db.query('select id, nome from public.perfis where id in ($1, $2) order by nome', [U.ana, U.beto])).rows;
	assert.deepEqual(r.map((x) => x.nome), ['Ana Souza', 'Nome beto']);
	await falha(como(U.ana, `update public.perfis set criado_em = now() where id = $1`, [U.ana]), /permission denied/);
	await falha(como(U.ana, `update public.perfis set nome = $2 where id = $1`, [U.ana, 'x'.repeat(121)]), /check constraint/);
	await como(U.ana, `update public.perfis set nome = 'Nome ana' where id = $1`, [U.ana]);
});

await teste('migração do apelido: nenhum apelido com @ sobrevive', async () => {
	// o arquivo roda de novo aqui com um apelido de e-mail plantado
	await db.query(`update public.membros set apelido = 'Prof' where papel = 'professor'`);
	await db.query(`update public.membros set apelido = 'fulano@gmail.co' where papel = 'professor'`);
	const sql = readFileSync(join(pastaMigracoes, '20261022030000_apelido_sem_email.sql'), 'utf8');
	await db.exec(sql);
	const r = (await db.query(`select apelido from public.membros where papel = 'professor'`)).rows;
	assert.deepEqual(r, [{ apelido: 'Sem nome' }]);
	await db.query(`update public.membros set apelido = 'Prof' where papel = 'professor'`);
});

await teste('anon não lê nada além de cursos', async () => {
	assert.equal((await como(null, 'select * from public.cursos')).length, 1);
	await falha(como(null, 'select * from public.respostas'), /permission denied/);
	await falha(como(null, `select public.entrar_turma('ENGC26', 'x', null, true, true)`), /permission denied/);
});

await teste('quem não é membro não acha a turma', async () => {
	assert.equal((await como(U.ana, 'select * from public.turmas')).length, 0);
});

await teste('entrar sem consentimento ou com código errado falha', async () => {
	await falha(como(U.ana, `select * from public.entrar_turma('ENGC26', 'Ana', null, true, false)`), /sem_consentimento/);
	await falha(como(U.ana, `select * from public.entrar_turma('XXXXXX', 'Ana', null, true, true)`), /codigo_invalido/);
});

await teste('entrar com código (minúsculo e espaço valem) e RA opcional', async () => {
	const r = await como(U.ana, `select nome from public.entrar_turma(' engc26 ', 'Ana', '123456', true, true)`);
	assert.deepEqual(r, [{ nome: 'Eng. Comp. 2026' }]);
	await como(U.beto, `select * from public.entrar_turma('ENGC26', 'Beto', null, false, true)`);
	assert.equal((await como(U.ana, 'select * from public.turmas')).length, 1);
});

await teste('entrar de novo atualiza a matrícula sem virar professor', async () => {
	await como(U.ana, `select * from public.entrar_turma('ENGC26', 'Aninha', '123456', true, true)`);
	const r = await como(U.ana, 'select apelido, papel from public.membros');
	assert.deepEqual(r, [{ apelido: 'Aninha', papel: 'aluno' }]);
});

await teste('dois alunos com o mesmo começo de nome entram (o ranking usa o nome)', async () => {
	await como(U.beto, `select * from public.entrar_turma('ENGC26', 'ANINHA', null, false, true)`);
	await como(U.beto, `select * from public.entrar_turma('ENGC26', 'Beto', null, false, true)`);
});

await teste('aluno não se promove a professor nem entra em turma direto', async () => {
	await falha(como(U.ana, `update public.membros set papel = 'professor'`), /permission denied/);
	await falha(
		como(U.intruso, `insert into public.membros (turma_id, usuario_id, apelido) values ($1, $2, 'x')`, [turma.id, U.intruso]),
		/permission denied/
	);
});

await teste('aluno vê só a própria matrícula; professor vê a turma', async () => {
	assert.equal((await como(U.ana, 'select * from public.membros')).length, 1);
	assert.equal((await como(U.prof, 'select * from public.membros')).length, 3);
});

await teste('resposta só se grava como si mesmo', async () => {
	const [r] = await resp(U.ana, '2019-CE-Q09', 'certa');
	assert.equal(r.usuario_id, U.ana);
	await falha(
		como(
			U.ana,
			`insert into public.respostas (id, usuario_id, questao_id, oficial, modo, resultado, respondida_em)
			 values (gen_random_uuid(), $1, '2019-CE-Q09', true, 'treino', 'certa', now())`,
			[U.beto]
		),
		/permission denied/
	);
});

await teste('reenviar a mesma resposta (mesmo id) não duplica', async () => {
	const id = '11111111-1111-1111-1111-111111111111';
	const sql = `insert into public.respostas (id, questao_id, oficial, materia, modo, resultado, respondida_em)
		values ($1, '2019-CE-Q10', true, 'algoritmos', 'treino', 'errada', now()) on conflict (id) do nothing`;
	await como(U.ana, sql, [id]);
	await como(U.ana, sql, [id]);
	const r = await como(U.ana, `select count(*)::int as n from public.respostas where id = $1`, [id]);
	assert.equal(r[0].n, 1);
});

await teste('resposta com data no futuro é recusada', async () => {
	await falha(resp(U.ana, '2019-CE-Q11', 'certa', { em: '2030-01-01' }), /check constraint/);
});

await teste('aluno lê só as próprias respostas', async () => {
	await resp(U.beto, '2019-CE-Q09', 'errada');
	await resp(U.beto, '2019-FG-Q01', 'certa', { parte: 'FG', materia: 'fg' });
	const r = await como(U.ana, 'select distinct usuario_id from public.respostas');
	assert.deepEqual(r, [{ usuario_id: U.ana }]);
	assert.equal((await como(U.prof, 'select * from public.respostas')).length, 0);
});

await teste('painel: professor vê alunos com nome e RA; aluno e intruso, nada', async () => {
	const r = await como(U.prof, 'select nome, apelido, ra, respondidas::int, certas::int from public.painel_alunos($1)', [turma.id]);
	assert.deepEqual(r, [
		{ nome: 'Nome ana', apelido: 'Aninha', ra: '123456', respondidas: 2, certas: 1 },
		{ nome: 'Nome beto', apelido: 'Beto', ra: null, respondidas: 2, certas: 1 }
	]);
	assert.equal((await como(U.ana, 'select * from public.painel_alunos($1)', [turma.id])).length, 0);
	assert.equal((await como(U.intruso, 'select * from public.painel_alunos($1)', [turma.id])).length, 0);
});

await teste('painel: questões mais erradas respeitam o mínimo de tentativas', async () => {
	const r = await como(U.prof, 'select questao_id, tentativas::int, erros::int from public.painel_questoes($1, 2)', [turma.id]);
	assert.deepEqual(r, [{ questao_id: '2019-CE-Q09', tentativas: 2, erros: 1 }]);
});

await teste('painel: matérias e semanas agregam a turma', async () => {
	const m = await como(U.prof, 'select materia, respondidas::int from public.painel_materias($1) order by materia', [turma.id]);
	assert.deepEqual(m, [
		{ materia: 'algoritmos', respondidas: 3 },
		{ materia: 'fg', respondidas: 1 }
	]);
	const s = await como(U.prof, 'select alunos_ativos::int, respondidas::int from public.painel_semanas($1)', [turma.id]);
	assert.deepEqual(s, [{ alunos_ativos: 2, respondidas: 4 }]);
});

await teste('ranking: mostra o nome do perfil, nunca o RA; quem saiu do ranking some (menos para si)', async () => {
	const ana = await como(U.ana, 'select apelido, eu from public.ranking_turma($1)', [turma.id]);
	assert.deepEqual(ana, [{ apelido: 'Nome ana', eu: true }]);
	const beto = await como(U.beto, 'select apelido, eu from public.ranking_turma($1)', [turma.id]);
	assert.deepEqual(beto.map((x) => x.apelido).sort(), ['Nome ana', 'Nome beto']);
	// trocar o nome muda o ranking na hora
	await como(U.ana, `update public.perfis set nome = 'Ana Souza' where id = $1`, [U.ana]);
	assert.equal((await como(U.ana, 'select apelido from public.ranking_turma($1)', [turma.id]))[0].apelido, 'Ana Souza');
	await como(U.ana, `update public.perfis set nome = 'Nome ana' where id = $1`, [U.ana]);
	assert.equal((await como(U.intruso, 'select * from public.ranking_turma($1)', [turma.id])).length, 0);
	const cols = Object.keys(beto[0]);
	assert.ok(!cols.includes('nome') && !cols.includes('ra'));
});

// --- simulado agendado (20261022000000_simulados_reportes.sql) ---------------
const PROVA = ['2019-FG-Q02', '2019-CE-Q09', '2019-CE-Q10', '2019-CE-D01'];
const criarSimulado = (usuario, abre = "now() - interval '1 hour'") =>
	como(
		usuario,
		`select id, titulo from public.criar_simulado($1, ' Simulado 1 ', $2, 3, ${abre}, now() + interval '7 days')`,
		[turma.id, PROVA]
	);
let simulado;

await teste('simulado: só o professor da turma agenda', async () => {
	await falha(criarSimulado(U.ana), /sem_permissao/);
	await falha(criarSimulado(U.intruso), /sem_permissao/);
	await falha(como(null, `select * from public.criar_simulado($1, 'x', '{}', 1, now(), now())`, [turma.id]), /permission denied/);
	[simulado] = await criarSimulado(U.prof);
	assert.equal(simulado.titulo, 'Simulado 1');
	await falha(como(U.ana, 'select * from public.simulados'), /permission denied/);
});

await teste('simulado: id de questão torto ou janela invertida são recusados', async () => {
	await falha(
		como(U.prof, `select * from public.criar_simulado($1, 'x1', '{"2019-CE-Q09; drop"}', 1, now(), now() + interval '1 day')`, [turma.id]),
		/check constraint/
	);
	await falha(
		como(U.prof, `select * from public.criar_simulado($1, 'x2', $2, 1, now(), now() - interval '1 day')`, [turma.id, PROVA]),
		/check constraint/
	);
});

await teste('simulado: membro vê a prova aberta; a futura vem sem as questões; intruso não vê', async () => {
	const [futuro] = await criarSimulado(U.prof, "now() + interval '2 days'");
	const ana = await como(U.ana, 'select id, questoes from public.simulados_turma($1)', [turma.id]);
	assert.deepEqual(ana.find((s) => s.id === simulado.id).questoes, PROVA);
	assert.equal(ana.find((s) => s.id === futuro.id).questoes, null);
	const prof = await como(U.prof, 'select id, questoes from public.simulados_turma($1)', [turma.id]);
	assert.deepEqual(prof.find((s) => s.id === futuro.id).questoes, PROVA);
	assert.equal((await como(U.intruso, 'select * from public.simulados_turma($1)', [turma.id])).length, 0);
	await falha(como(U.ana, 'select public.apagar_simulado($1)', [futuro.id]), /sem_permissao/);
	await como(U.prof, 'select public.apagar_simulado($1)', [futuro.id]);
	assert.equal((await como(U.prof, 'select * from public.simulados_turma($1)', [turma.id])).length, 1);
});

const respSim = (usuario, questao, resultado, simuladoId, em = null) =>
	como(
		usuario,
		`insert into public.respostas (id, questao_id, oficial, parte, materia, modo, resultado, respondida_em, simulado_id)
		 values (gen_random_uuid(), $1, true, 'CE', 'algoritmos', 'simulado', $2, coalesce($4::timestamptz, now()), $3)
		 returning simulado_id`,
		[questao, resultado, simuladoId, em]
	);

await teste('simulado: resposta de fora da turma entra sem o vínculo (a fila não trava)', async () => {
	const [r] = await respSim(U.intruso, '2019-CE-Q09', 'certa', simulado.id);
	assert.equal(r.simulado_id, null);
	const [r2] = await respSim(U.ana, '2019-CE-Q09', 'certa', '99999999-9999-9999-9999-999999999999');
	assert.equal(r2.simulado_id, null);
});

await teste('simulado: painel conta a primeira resposta e ignora a discursiva', async () => {
	await respSim(U.ana, '2019-CE-Q09', 'certa', simulado.id, '2026-10-22T10:00:00Z');
	await respSim(U.ana, '2019-CE-Q10', 'errada', simulado.id, '2026-10-22T10:00:00Z');
	await respSim(U.ana, '2019-CE-D01', 'certa', simulado.id, '2026-10-22T10:00:00Z');
	// refez depois da correção: não muda a nota
	await respSim(U.ana, '2019-CE-Q10', 'certa', simulado.id, '2026-10-22T11:00:00Z');
	const r = await como(U.prof, 'select apelido, respondidas::int, certas::int from public.painel_simulado($1)', [simulado.id]);
	assert.deepEqual(r, [
		{ apelido: 'Aninha', respondidas: 2, certas: 1 },
		{ apelido: 'Beto', respondidas: 0, certas: 0 }
	]);
	const q = await como(U.prof, 'select questao_id, respondidas::int, certas::int from public.painel_simulado_questoes($1)', [simulado.id]);
	assert.deepEqual(q, [
		{ questao_id: '2019-CE-Q10', respondidas: 1, certas: 0 },
		{ questao_id: '2019-CE-Q09', respondidas: 1, certas: 1 }
	]);
	assert.equal((await como(U.ana, 'select * from public.painel_simulado($1)', [simulado.id])).length, 0);
	assert.equal((await como(U.ana, 'select * from public.painel_simulado_questoes($1)', [simulado.id])).length, 0);
});

// --- ficha do aluno (20261022040000_ficha_do_aluno.sql) -------------------
await teste('ficha: professor vê o aluno da turma; aluno, intruso e aluno de fora, nada', async () => {
	const [{ f }] = await como(U.prof, 'select public.painel_aluno($1, $2) as f', [turma.id, U.ana]);
	assert.equal(f.perfil.nome, 'Nome ana');
	assert.equal(f.perfil.ra, '123456');
	assert.ok(Number(f.total) >= 5);
	assert.ok(f.dias.length >= 1);
	// Q10: errada (reenvio, agora), errada e certa (no simulado, de manhã)
	const q10 = f.erradas.find((q) => q.questao_id === '2019-CE-Q10');
	assert.deepEqual([q10.tentativas, q10.erros, q10.ultima_certa], [3, 2, false]);
	const sim = f.simulados.find((s) => s.id === simulado.id);
	assert.deepEqual([sim.respondidas, sim.certas], [2, 1]);
	assert.equal((await como(U.ana, 'select public.painel_aluno($1, $2) as f', [turma.id, U.ana]))[0].f, null);
	assert.equal((await como(U.intruso, 'select public.painel_aluno($1, $2) as f', [turma.id, U.ana]))[0].f, null);
	// o intruso não é aluno da turma: o professor não lê a ficha dele
	assert.equal((await como(U.prof, 'select public.painel_aluno($1, $2) as f', [turma.id, U.intruso]))[0].f, null);
	await falha(como(null, 'select public.painel_aluno($1, $2)', [turma.id, U.ana]), /permission denied/);
});

// --- primeira tentativa e alternativa marcada (D16) -----------------------
const respLetra = (usuario, questao, resultado, escolha, em) =>
	como(
		usuario,
		`insert into public.respostas (id, questao_id, oficial, parte, materia, modo, resultado, escolha, respondida_em)
		 values (gen_random_uuid(), $1, true, 'CE', 'redes', 'treino', $2, $3, $4::timestamptz)`,
		[questao, resultado, escolha, em]
	);

await teste('D16: refazer até acertar não infla o acerto da turma', async () => {
	await respLetra(U.ana, '2019-CE-Q20', 'errada', 'C', '2026-10-20T10:00:00Z');
	await respLetra(U.ana, '2019-CE-Q20', 'certa', 'B', '2026-10-20T10:05:00Z');
	await respLetra(U.ana, '2019-CE-Q20', 'certa', 'B', '2026-10-20T10:06:00Z');
	await respLetra(U.beto, '2019-CE-Q20', 'errada', 'C', '2026-10-20T11:00:00Z');
	const [m] = await como(U.prof, `select respondidas::int, certas::int from public.painel_materias($1) where materia = 'redes'`, [turma.id]);
	assert.deepEqual(m, { respondidas: 2, certas: 0 });
	const a = await como(U.prof, 'select apelido, primeiras::int, primeiras_certas::int from public.painel_alunos($1)', [turma.id]);
	assert.deepEqual(a.find((x) => x.apelido === 'Aninha'), { apelido: 'Aninha', primeiras: 3, primeiras_certas: 1 });
});

await teste('D16: por questão, a alternativa errada mais marcada', async () => {
	const [q] = await como(
		U.prof,
		`select tentativas::int, erros::int, escolha_comum, escolha_comum_n::int, erros_com_escolha::int
		 from public.painel_questoes($1, 2) where questao_id = '2019-CE-Q20'`,
		[turma.id]
	);
	assert.deepEqual(q, { tentativas: 2, erros: 2, escolha_comum: 'C', escolha_comum_n: 2, erros_com_escolha: 2 });
	await falha(respLetra(U.ana, '2019-CE-Q21', 'errada', 'Z', '2026-10-20T12:00:00Z'), /check constraint/);
});

await teste('D16: ranking conta questões diferentes, repetir não sobe ninguém', async () => {
	const antes = (await como(U.ana, 'select certas::int from public.ranking_turma($1) where eu', [turma.id]))[0].certas;
	await respLetra(U.ana, '2019-CE-Q20', 'certa', 'B', '2026-10-20T13:00:00Z');
	await respLetra(U.ana, '2019-CE-Q20', 'certa', 'B', '2026-10-20T13:01:00Z');
	const depois = (await como(U.ana, 'select certas::int from public.ranking_turma($1) where eu', [turma.id]))[0].certas;
	assert.equal(depois, antes);
});

await teste('D16: resumo dos simulados (participação e média de quem fez)', async () => {
	const r = await como(U.prof, 'select titulo, alunos_fizeram::int, media_certas::float from public.painel_simulados_resumo($1)', [turma.id]);
	assert.deepEqual(r, [{ titulo: 'Simulado 1', alunos_fizeram: 1, media_certas: 1 }]);
	assert.equal((await como(U.ana, 'select * from public.painel_simulados_resumo($1)', [turma.id])).length, 0);
});

// --- reporte de erro -------------------------------------------------------
await teste('reporte: anônimo e logado reportam; ninguém lê pelo site', async () => {
	await como(null, `select public.reportar_questao('2019-CE-Q09', 'gabarito', 'A letra certa é a C')`);
	await como(U.ana, `select public.reportar_questao('2019-CE-Q10', 'enunciado', '')`);
	const r = (await db.query('select usuario_id, motivo from public.reportes order by criado_em')).rows;
	assert.deepEqual(r, [
		{ usuario_id: null, motivo: 'gabarito' },
		{ usuario_id: U.ana, motivo: 'enunciado' }
	]);
	await falha(como(U.ana, 'select * from public.reportes'), /permission denied/);
	await falha(como(null, `select public.reportar_questao('2019-CE-Q09', 'xingamento', '')`), /check constraint/);
});

await teste('reporte: teto por hora segura enxurrada', async () => {
	for (let k = 0; k < 19; k++) await como(U.ana, `select public.reportar_questao('2019-CE-Q11', 'outro', '')`);
	await falha(como(U.ana, `select public.reportar_questao('2019-CE-Q11', 'outro', '')`), /muitos_reportes/);
});

// --- visitas (20261022010000_visitas.sql) ---------------------------------
const APARELHO = '22222222-2222-4222-8222-222222222222';
const visita = (usuario, caminho, extra = {}) =>
	como(usuario, `select public.registrar_visita($1, $2, $3, $4, $5, $6)`, [
		extra.aparelho ?? APARELHO,
		caminho,
		extra.convite ?? false,
		extra.origem ?? null,
		!!usuario,
		extra.tela ?? 'celular'
	]);

await teste('visitas: anônimo e logado registram; ninguém lê pelo site', async () => {
	await visita(null, '/conta/', { convite: true, origem: 'WhatsApp.com' });
	await visita(U.ana, '/treino/');
	const r = (await db.query('select caminho, convite, origem, logado from public.visitas order by id')).rows;
	assert.deepEqual(r, [
		{ caminho: '/conta/', convite: true, origem: 'whatsapp.com', logado: false },
		{ caminho: '/treino/', convite: false, origem: null, logado: true }
	]);
	await falha(como(null, 'select * from public.visitas'), /permission denied/);
	await falha(como(U.ana, 'select * from public.visitas_por_dia'), /permission denied/);
	const [d] = (await db.query('select visitas::int, pessoas::int, abriram_convite::int from public.visitas_por_dia')).rows;
	assert.deepEqual(d, { visitas: 2, pessoas: 1, abriram_convite: 1 });
});

await teste('visitas: caminho com query ou origem com endereço inteiro são recusados', async () => {
	await falha(visita(null, '/conta/?turma=ENGC26'), /check constraint/);
	await falha(visita(null, '/', { origem: 'https://evil.com/x?y' }), /check constraint/);
});

await teste('visitas: teto por aparelho ignora o excesso sem dar erro', async () => {
	const outro = '33333333-3333-4333-8333-333333333333';
	for (let k = 0; k < 125; k++) await visita(null, '/', { aparelho: outro });
	const [{ n }] = (await db.query('select count(*)::int as n from public.visitas where aparelho = $1', [outro])).rows;
	assert.equal(n, 120);
});

await teste('sair da turma tira do painel, mas mantém as respostas do aluno', async () => {
	await como(U.beto, 'delete from public.membros');
	assert.equal((await como(U.prof, 'select * from public.painel_alunos($1)', [turma.id])).length, 1);
	assert.equal((await como(U.beto, 'select * from public.respostas')).length, 3); // 2 + a Q20 do teste D16
});

await teste('apagar a conta leva perfil e respostas junto', async () => {
	await como(U.ana, 'select public.apagar_minha_conta()');
	assert.equal((await db.query(`select * from public.respostas where usuario_id = $1`, [U.ana])).rows.length, 0);
	assert.equal((await db.query(`select * from public.perfis where id = $1`, [U.ana])).rows.length, 0);
});

console.log(`\n${n} testes passaram`);
