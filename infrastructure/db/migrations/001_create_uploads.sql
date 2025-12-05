-- create uploads table
-- Uses pgcrypto for gen_random_uuid(); if unavailable, user will need to enable pgcrypto or replace with uuid_generate_v4()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS uploads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  filename TEXT NOT NULL,
  total_size BIGINT NOT NULL,
  chunk_count INT NOT NULL,
  chunk_size INT NOT NULL,
  uploaded_chunks JSONB NOT NULL DEFAULT '[]'::jsonb,
  status TEXT NOT NULL DEFAULT 'in_progress',
  checksum TEXT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
