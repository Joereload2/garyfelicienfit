-- GaryFelicienFit / PlanFit
-- Pégalo en Supabase → SQL Editor → Run.
-- Usa la service_role key solo en el servidor, nunca en el navegador.

create table if not exists public.entitlements (
  token text primary key,
  email text not null,
  payment_ref text not null unique,
  status text not null default 'pending' check (status in ('pending', 'used')),
  url text,
  created_at timestamptz not null default now(),
  used_at timestamptz,
  pdf_path text,
  pdf_filename text,
  submission jsonb
);

create index if not exists entitlements_email_idx on public.entitlements (email);
create index if not exists entitlements_status_idx on public.entitlements (status);

create table if not exists public.coaching_leads (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  email text not null,
  phone text,
  message text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.mail_log (
  id uuid primary key default gen_random_uuid(),
  kind text not null,
  to_email text not null,
  subject text not null,
  body text,
  payment_ref text,
  provider text,
  status text not null,
  error text,
  created_at timestamptz not null default now()
);

create table if not exists public.payments (
  id uuid primary key default gen_random_uuid(),
  provider text not null,
  provider_id text unique,
  email text not null,
  payment_ref text not null,
  amount_cents int,
  currency text default 'usd',
  status text not null,
  raw jsonb,
  created_at timestamptz not null default now()
);

alter table public.entitlements enable row level security;
alter table public.coaching_leads enable row level security;
alter table public.mail_log enable row level security;
alter table public.payments enable row level security;

-- Sin policies públicas: el anon key no lee ni escribe. Solo service_role.

insert into storage.buckets (id, name, public)
values ('pdfs', 'pdfs', false)
on conflict (id) do nothing;
