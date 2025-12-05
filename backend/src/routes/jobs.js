// backend/src/routes/jobs.js
// Job producer: creates jobs in DB and pushes to Redis queue for worker consumption.
const express = require('express');
const pool = require('../db/pool');
const Redis = require('ioredis');
const redis = new Redis(process.env.REDIS_URL || 'redis://redis:6379/0');
const router = express.Router();

// POST /api/jobs — create a new job
router.post('/', async (req, res) => {
  try {
    const { dataset_id, params } = req.body || {};
    const result = await pool.query(
      `INSERT INTO jobs(dataset_id, params, status) VALUES($1,$2,$3) RETURNING id, created_at, status`,
      [dataset_id || null, JSON.stringify(params || {}), 'queued']
    );
    const job_id = result.rows[0].id;
    
    // Push job_id to Redis queue for worker consumption
    await redis.lpush('bioml:jobs', job_id);
    console.log(`[jobs] created job ${job_id}, pushed to queue`);
    
    return res.status(201).json({ 
      job_id, 
      status: result.rows[0].status,
      created_at: result.rows[0].created_at 
    });
  } catch (err) {
    console.error('[jobs] error:', err);
    return res.status(500).json({ error: 'job create failed', details: err.message });
  }
});

// GET /api/jobs/:job_id — get job status
router.get('/:job_id', async (req, res) => {
  try {
    const { job_id } = req.params;
    const result = await pool.query(
      `SELECT id, status, params, result_payload, created_at, updated_at FROM jobs WHERE id=$1`,
      [job_id]
    );
    if (result.rows.length === 0) return res.status(404).json({ error: 'job not found' });
    return res.json(result.rows[0]);
  } catch (err) {
    console.error('[jobs] error:', err);
    return res.status(500).json({ error: 'job fetch failed' });
  }
});

module.exports = router;
