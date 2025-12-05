-- 002_create_jobs_and_artifacts.sql
-- Jobs and artifacts tables for the Redis-backed job queue.
-- Uses gen_random_uuid() from pgcrypto extension (enabled in 001_create_uploads.sql).

CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dataset_id UUID NULL,
  user_id UUID NULL,
  params JSONB DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'queued',
  result_payload JSONB NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS artifacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  path TEXT NOT NULL,
  checksum TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_artifacts_job_id ON artifacts(job_id);
