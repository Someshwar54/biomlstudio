// backend/src/routes/jobs.js
const express = require('express');
const pool = require('../db/pool');
const router = express.Router();

// Create job: POST /api/jobs { dataset_id, params }
router.post('/', async (req, res) => {
  try {
    const { dataset_id, params } = req.body;
    const jobParams = params || {};
    
    const result = await pool.query(
      'INSERT INTO jobs(dataset_id, params, status) VALUES($1, $2, $3) RETURNING id, dataset_id, params, status, created_at',
      [dataset_id || null, JSON.stringify(jobParams), 'pending']
    );
    
    const job = result.rows[0];
    return res.status(201).json({
      job_id: job.id,
      dataset_id: job.dataset_id,
      params: job.params,
      status: job.status,
      created_at: job.created_at
    });
  } catch (err) {
    console.error('Create job failed:', err);
    return res.status(500).json({ error: 'job creation failed' });
  }
});

// Get job: GET /api/jobs/:job_id
router.get('/:job_id', async (req, res) => {
  try {
    const { job_id } = req.params;
    const result = await pool.query('SELECT * FROM jobs WHERE id=$1', [job_id]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'job not found' });
    }
    
    return res.json(result.rows[0]);
  } catch (err) {
    console.error('Get job failed:', err);
    return res.status(500).json({ error: 'get job failed' });
  }
});

// Update job status: PATCH /api/jobs/:job_id { status, result_payload }
router.patch('/:job_id', async (req, res) => {
  try {
    const { job_id } = req.params;
    const { status, result_payload } = req.body;
    
    let query = 'UPDATE jobs SET updated_at=now()';
    const params = [];
    let paramCount = 1;
    
    if (status) {
      params.push(status);
      query += `, status=$${paramCount++}`;
    }
    
    if (result_payload) {
      params.push(JSON.stringify(result_payload));
      query += `, result_payload=$${paramCount++}`;
    }
    
    params.push(job_id);
    query += ` WHERE id=$${paramCount} RETURNING *`;
    
    const result = await pool.query(query, params);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'job not found' });
    }
    
    return res.json(result.rows[0]);
  } catch (err) {
    console.error('Update job failed:', err);
    return res.status(500).json({ error: 'update job failed' });
  }
});

module.exports = router;
