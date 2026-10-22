// Dublê LOCAL do Supabase para desenvolver as telas de conta/turma/painel sem
// projeto na nuvem. Roda a migração de verdade num Postgres em memória (PGlite)
// e imita só o pedaço do Auth e do PostgREST que o `app/src/lib/nuvem.js` usa.
// A RLS e as funções `painel_*` valem como no Supabase.
//
//   cd supabase/testes && npm install
//   node servidor-local.mjs                  # http://127.0.0.1:54321
//   # em outro terminal, dentro de app/:
//   VITE_SUPABASE_URL=http://127.0.0.1:54321 VITE_SUPABASE_ANON_KEY=local npm run dev
//
// "Entrar com Google" abre uma página daqui para escolher quem você é
// (professor, Ana, Beto ou um aluno novo). A turma de exemplo tem o código
// ENGC26. NÃO é seguro: o token não tem assinatura. Só para a sua máquina.

import { createServer } from 'node:http';
import { randomUUID } from 'node:crypto';
import { readFileSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { PGlite } from '@electric-sql/pglite';

const PORTA = Number(process.env.PORTA || 54321);
const aqui = dirname(fileURLToPath(import.meta.url));

const db = new PGlite();
await db.exec(`
	create role anon nologin;
	create role authenticated nologin;
	create schema auth;
	grant usage on schema auth to anon, authenticated;
	create table auth.users (id uuid primary key, email text, raw_user_meta_data jsonb not null default '{}');
	create function auth.uid() returns uuid language sql stable as
		$$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
	grant execute on function auth.uid() to anon, authenticated;
	grant usage on schema public to anon, authenticated;
`);
const pasta = join(aqui, '..', 'migrations');
for (const f of readdirSync(pasta).filter((f) => f.endsWith('.sql')).sort()) {
	await db.exec(readFileSync(join(pasta, f), 'utf8'));
}

// --- dados de exemplo -------------------------------------------------------
const PESSOAS = {
	prof: { id: '00000000-0000-4000-8000-00000000000a', nome: 'Professora Exemplo', email: 'prof@exemplo.com' },
	ana: { id: '00000000-0000-4000-8000-00000000000b', nome: 'Ana Souza', email: 'ana@exemplo.com' },
	beto: { id: '00000000-0000-4000-8000-00000000000c', nome: 'Beto Lima', email: 'beto@exemplo.com' }
};
for (const p of Object.values(PESSOAS)) {
	await db.query(`insert into auth.users (id, email, raw_user_meta_data) values ($1, $2, $3)`, [
		p.id,
		p.email,
		JSON.stringify({ full_name: p.nome })
	]);
}
const {
	rows: [turma]
} = await db.query(
	`insert into public.turmas (curso, instituicao, nome, data_prova, codigo)
	 values ('engcomp', 'Unisalesiano', 'Eng. de Computação 2026', '2026-11-29', 'ENGC26') returning id`
);
await db.query(`insert into public.membros (turma_id, usuario_id, papel, apelido) values ($1, $2, 'professor', 'Prof')`, [
	turma.id,
	PESSOAS.prof.id
]);
for (const [k, apelido, ra] of [
	['ana', 'Aninha', '20231234'],
	['beto', 'Beto', null]
]) {
	await db.query(`insert into public.membros (turma_id, usuario_id, apelido, ra) values ($1, $2, $3, $4)`, [
		turma.id,
		PESSOAS[k].id,
		apelido,
		ra
	]);
}
// algumas respostas espalhadas em 3 semanas, para o painel não nascer vazio
const exemplo = [
	['ana', '2019-CE-Q09', 'algoritmos', 'certa', 1],
	['ana', '2019-CE-Q10', 'ciencia-dados', 'errada', 1],
	['ana', '2023-CE-Q15', 'algoritmos', 'errada', 8],
	['ana', '2019-FG-Q02', 'textos', 'certa', 15],
	['beto', '2019-CE-Q09', 'algoritmos', 'errada', 2],
	['beto', '2023-CE-Q15', 'algoritmos', 'errada', 9],
	['beto', '2019-CE-Q10', 'ciencia-dados', 'errada', 3],
	['ana', '2023-CE-Q15', 'algoritmos', 'certa', 0]
];
for (const [k, q, materia, resultado, diasAtras] of exemplo) {
	await db.query(
		`insert into public.respostas (id, usuario_id, questao_id, oficial, parte, materia, modo, resultado, duracao_ms, respondida_em)
		 values ($1, $2, $3, true, $4, $5, 'treino', $6, 40000, now() - make_interval(days => $7))`,
		[randomUUID(), PESSOAS[k].id, q, q.includes('-FG-') ? 'FG' : 'CE', materia, resultado, diasAtras]
	);
}

// --- SQL como um usuário ----------------------------------------------------
async function como(sub, sql, params = []) {
	return db.transaction(async (tx) => {
		await tx.query(`select set_config('request.jwt.claim.sub', $1, true)`, [sub ?? '']);
		await tx.exec(sub ? 'set local role authenticated' : 'set local role anon');
		return (await tx.query(sql, params)).rows;
	});
}

// --- Auth falso -------------------------------------------------------------
const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
const codigos = new Map(); // código PKCE → id do usuário

async function sessao(id) {
	const {
		rows: [u]
	} = await db.query(`select id, email, raw_user_meta_data from auth.users where id = $1`, [id]);
	const exp = Math.floor(Date.now() / 1000) + 3600;
	return {
		access_token: `${b64({ alg: 'none', typ: 'JWT' })}.${b64({ sub: id, role: 'authenticated', exp })}.x`,
		token_type: 'bearer',
		expires_in: 3600,
		expires_at: exp,
		refresh_token: `r-${id}`,
		user: {
			id,
			aud: 'authenticated',
			role: 'authenticated',
			email: u.email,
			user_metadata: u.raw_user_meta_data,
			app_metadata: { provider: 'google' },
			created_at: new Date().toISOString()
		}
	};
}

function subDoToken(req) {
	const t = (req.headers.authorization || '').replace(/^Bearer /, '');
	try {
		const p = JSON.parse(Buffer.from(t.split('.')[1] || '', 'base64url').toString());
		return p.role === 'authenticated' ? p.sub : null;
	} catch {
		return null;
	}
}

function paginaEscolha(volta) {
	const op = Object.entries(PESSOAS)
		.map(([k, p]) => `<li><a href="/auth/v1/escolher?como=${k}&volta=${encodeURIComponent(volta)}">${p.nome}</a></li>`)
		.join('');
	return `<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">
	<title>Login local</title><body style="font:16px system-ui;padding:24px;max-width:420px;margin:auto">
	<h1 style="font-size:20px">Login local (dublê do Google)</h1><ul style="line-height:2.2">${op}
	<li><a href="/auth/v1/escolher?como=novo&volta=${encodeURIComponent(volta)}">Aluno novo (sem turma)</a></li></ul>`;
}

// --- PostgREST mínimo -------------------------------------------------------
const FUNCOES = new Set([
	'entrar_turma',
	'apagar_minha_conta',
	'ranking_turma',
	'painel_alunos',
	'painel_materias',
	'painel_questoes',
	'painel_semanas',
	'criar_simulado',
	'apagar_simulado',
	'simulados_turma',
	'painel_simulado',
	'painel_simulado_questoes',
	'reportar_questao',
	'registrar_visita'
]);
// devolvem `void`: o PostgREST responde `null`, não uma linha
const FUNCOES_VOID = new Set(['apagar_minha_conta', 'apagar_simulado', 'reportar_questao', 'registrar_visita']);

function erroPg(res, e) {
	const status = /permission denied|row-level/.test(e.message) ? 403 : 400;
	json(res, status, { code: e.code ?? 'P0001', message: e.message, details: null, hint: null });
}

function json(res, status, corpo) {
	res.writeHead(status, { 'content-type': 'application/json' });
	res.end(corpo === undefined ? '' : JSON.stringify(corpo));
}

async function lerCorpo(req) {
	let s = '';
	for await (const c of req) s += c;
	if (!s) return {};
	return req.headers['content-type']?.includes('json') ? JSON.parse(s) : Object.fromEntries(new URLSearchParams(s));
}

const servidor = createServer(async (req, res) => {
	res.setHeader('access-control-allow-origin', req.headers.origin || '*');
	res.setHeader('access-control-allow-credentials', 'true');
	res.setHeader('access-control-allow-headers', req.headers['access-control-request-headers'] || '*');
	res.setHeader('access-control-allow-methods', 'GET,POST,PATCH,DELETE,OPTIONS');
	res.setHeader('access-control-expose-headers', 'content-range');
	if (req.method === 'OPTIONS') return res.writeHead(204).end();

	const url = new URL(req.url, `http://${req.headers.host}`);
	const sub = subDoToken(req);
	try {
		// ---- auth
		if (url.pathname === '/auth/v1/authorize') {
			const volta = url.searchParams.get('redirect_to') || '/';
			res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
			return res.end(paginaEscolha(volta));
		}
		if (url.pathname === '/auth/v1/escolher') {
			let id = PESSOAS[url.searchParams.get('como')]?.id;
			if (!id) {
				id = randomUUID();
				const n = Math.floor(Math.random() * 900 + 100);
				await db.query(`insert into auth.users (id, email, raw_user_meta_data) values ($1, $2, $3)`, [
					id,
					`aluno${n}@exemplo.com`,
					JSON.stringify({ full_name: `Aluno Novo ${n}` })
				]);
			}
			const codigo = randomUUID();
			codigos.set(codigo, id);
			const volta = new URL(url.searchParams.get('volta'));
			volta.searchParams.set('code', codigo);
			res.writeHead(302, { location: volta.href });
			return res.end();
		}
		if (url.pathname === '/auth/v1/token') {
			const corpo = await lerCorpo(req);
			const tipo = url.searchParams.get('grant_type');
			const id = tipo === 'pkce' ? codigos.get(corpo.auth_code) : String(corpo.refresh_token || '').slice(2);
			if (!id) return json(res, 400, { error: 'invalid_grant', error_description: 'código inválido' });
			codigos.delete(corpo.auth_code);
			return json(res, 200, await sessao(id));
		}
		if (url.pathname === '/auth/v1/user') {
			if (!sub) return json(res, 401, { message: 'sem sessão' });
			return json(res, 200, (await sessao(sub)).user);
		}
		if (url.pathname === '/auth/v1/otp') return json(res, 200, {});
		if (url.pathname === '/auth/v1/logout') return res.writeHead(204).end();

		// ---- rpc
		const rpc = /^\/rest\/v1\/rpc\/([a-z_]+)$/.exec(url.pathname);
		if (rpc && req.method === 'POST') {
			if (!FUNCOES.has(rpc[1])) return json(res, 404, { code: 'PGRST202', message: 'função não existe' });
			const args = await lerCorpo(req);
			const nomes = Object.keys(args);
			const lista = nomes.map((k, i) => `${k} => $${i + 1}`).join(', ');
			const linhas = await como(sub, `select * from public.${rpc[1]}(${lista})`, nomes.map((k) => args[k]));
			return json(res, 200, FUNCOES_VOID.has(rpc[1]) ? null : linhas);
		}

		// ---- tabelas que o app usa
		if (url.pathname === '/rest/v1/membros' && req.method === 'GET') {
			const linhas = await como(
				sub,
				`select m.papel, m.apelido, m.ra, m.no_ranking, m.entrou_em,
					json_build_object('id', t.id, 'nome', t.nome, 'instituicao', t.instituicao, 'curso', t.curso,
						'data_prova', t.data_prova, 'codigo', t.codigo, 'ranking_ativo', t.ranking_ativo) as turma
				 from public.membros m join public.turmas t on t.id = m.turma_id
				 where m.usuario_id = auth.uid()
				 order by m.entrou_em`
			);
			return json(res, 200, linhas);
		}
		if (url.pathname === '/rest/v1/membros' && req.method === 'DELETE') {
			const t = (url.searchParams.get('turma_id') || '').replace(/^eq\./, '');
			await como(sub, `delete from public.membros where turma_id = $1`, [t]);
			return res.writeHead(204).end();
		}
		if (url.pathname === '/rest/v1/respostas' && req.method === 'POST') {
			const corpo = await lerCorpo(req);
			const linhas = Array.isArray(corpo) ? corpo : [corpo];
			await como(
				sub,
				`insert into public.respostas (id, curso, questao_id, oficial, parte, materia, modo, resultado, duracao_ms, respondida_em, simulado_id)
				 select id, curso, questao_id, oficial, parte, materia, modo, resultado, duracao_ms, respondida_em, simulado_id
				 from json_populate_recordset(null::public.respostas, $1::json)
				 on conflict (id) do nothing`,
				[JSON.stringify(linhas)]
			);
			console.log(`respostas: +${linhas.length} de ${sub}`);
			return res.writeHead(201).end();
		}
		json(res, 404, { message: `não implementado no dublê: ${req.method} ${url.pathname}` });
	} catch (e) {
		erroPg(res, e);
	}
});

servidor.listen(PORTA, '127.0.0.1', () => {
	console.log(`Supabase dublê em http://127.0.0.1:${PORTA}  (turma de exemplo: ENGC26)`);
});
