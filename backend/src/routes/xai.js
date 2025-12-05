// backend/src/routes/xai.js
const express = require('express');
const pool = require('../db/pool');
const Redis = require('ioredis');
const { requireAuth } = require('../middleware/auth');
const redis = new Redis(process.env.REDIS_URL || 'redis://redis:6379/0');
const router = express.Router();

router.post('/request', requireAuth, async (req,res)=>{
  const {job_id, model_path, sample} = req.body;
  const q = await pool.query('INSERT INTO xai_jobs(job_id, requester, model_path, status) VALUES($1,$2,$3,$4) RETURNING id',[job_id, req.user.sub, model_path, 'queued']);
  const xai_id = q.rows[0].id;
  await redis.lpush('bioml:xai', xai_id);
  res.json({xai_id});
});

router.get('/:xai_id', requireAuth, async (req,res)=>{
  const id=req.params.xai_id;
  const q = await pool.query('SELECT status,result_path FROM xai_jobs WHERE id=$1',[id]);
  if(!q.rows.length) return res.status(404).json({error:'not found'});
  const r=q.rows[0];
  if(r.result_path && require('fs').existsSync(r.result_path)) {
    return res.sendFile(require('path').resolve(r.result_path));
  }
  return res.json({status:r.status});
});

module.exports = router;