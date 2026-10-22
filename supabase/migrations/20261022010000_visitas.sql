-- Visitas ao site: quantas pessoas abrem, por onde chegam e quantas abrem o
-- convite da turma sem chegar a entrar (o funil que o painel não via).
--
-- Roda DEPOIS de 20261022000000_simulados_reportes.sql. O site funciona sem
-- este arquivo: o envio da visita só falha em silêncio.
--
-- D14 (docs/DECISOES.md): contagem própria, no mesmo banco, enquanto o P5
-- (analytics de produto) não chega. Nada de nome, e-mail ou IP: o
-- `aparelho` é um uuid sorteado no navegador (localStorage), sem ligação com
-- a conta, só para contar pessoas em vez de cliques.

create table public.visitas (
	id bigint generated always as identity primary key,
	aparelho uuid not null,
	caminho text not null check (caminho ~ '^/[a-z0-9/-]{0,60}$'),
	-- veio pelo link do convite (/conta/?turma=…)
	convite boolean not null default false,
	-- domínio de onde veio (whatsapp.com, google.com…), nunca o endereço inteiro
	origem text check (origem ~ '^[a-z0-9.-]{1,100}$'),
	logado boolean not null default false,
	tela text check (tela in ('celular', 'computador')),
	criado_em timestamptz not null default now()
);

create index visitas_data on public.visitas (criado_em desc);
create index visitas_aparelho on public.visitas (aparelho, criado_em desc);

alter table public.visitas enable row level security;
revoke all on public.visitas from anon, authenticated;

create function public.registrar_visita(
	p_aparelho uuid,
	p_caminho text,
	p_convite boolean default false,
	p_origem text default null,
	p_logado boolean default false,
	p_tela text default null
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
	-- teto por aparelho: um script em loop não enche a tabela
	if (select count(*) from public.visitas v
		where v.aparelho = p_aparelho and v.criado_em > now() - interval '1 hour') >= 120 then
		return;
	end if;
	insert into public.visitas (aparelho, caminho, convite, origem, logado, tela)
	values (
		p_aparelho,
		p_caminho,
		coalesce(p_convite, false),
		nullif(lower(left(btrim(coalesce(p_origem, '')), 100)), ''),
		coalesce(p_logado, false),
		p_tela
	);
end;
$$;

revoke all on function public.registrar_visita(uuid, text, boolean, text, boolean, text) from public;
grant execute on function public.registrar_visita(uuid, text, boolean, text, boolean, text) to anon, authenticated;

-- Resumo por dia, para abrir no Table Editor (ninguém lê pelo site).
-- `security_invoker`: a view respeita as permissões de quem consulta.
create view public.visitas_por_dia with (security_invoker = true) as
select
	(v.criado_em at time zone 'America/Sao_Paulo')::date as dia,
	count(*) as visitas,
	count(distinct v.aparelho) as pessoas,
	count(distinct v.aparelho) filter (where v.convite) as abriram_convite,
	count(distinct v.aparelho) filter (where v.logado) as logadas,
	count(distinct v.aparelho) filter (where v.tela = 'celular') as no_celular
from public.visitas v
group by 1
order by 1 desc;

revoke all on public.visitas_por_dia from anon, authenticated;
