-- Run this in the Supabase SQL Editor (https://app.supabase.com → SQL Editor)

create table if not exists sentiment_analyses (
  id           uuid primary key default gen_random_uuid(),
  analyzed_at  timestamptz not null default now(),
  stock        text not null,
  sentiment_score integer not null check (sentiment_score in (-1, 0, 1)),
  signal       text not null,
  summary      text not null
);

-- Index for fast history queries
create index if not exists idx_sentiment_analyses_analyzed_at
  on sentiment_analyses (analyzed_at desc);

-- Row Level Security: allow public read/insert (anon key)
alter table sentiment_analyses enable row level security;

create policy "allow anon read"
  on sentiment_analyses for select
  using (true);

create policy "allow anon insert"
  on sentiment_analyses for insert
  with check (true);
