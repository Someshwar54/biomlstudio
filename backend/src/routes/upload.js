// backend/src/routes/upload.js
const express = require('express');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const pool = require('../db/pool'); // assume pool exports pg Pool instance
const router = express.Router();

const UPLOAD_TMP_DIR = path.resolve(process.cwd(), 'data', 'uploads', 'tmp');
const UPLOAD_DIR = path.resolve(process.cwd(), 'data', 'uploads');
fs.mkdirSync(UPLOAD_TMP_DIR, { recursive: true });
fs.mkdirSync(UPLOAD_DIR, { recursive: true });

// Init upload: POST /api/upload/init { filename, total_size, chunk_size }
router.post('/init', async (req, res) => {
  try {
    const { filename, total_size, chunk_size } = req.body;
    if (!filename || !total_size || !chunk_size) return res.status(400).json({ error: 'missing params' });
    const chunk_count = Math.ceil(total_size / chunk_size);
    const result = await pool.query(
      `INSERT INTO uploads(filename, total_size, chunk_count, chunk_size, uploaded_chunks, status)
       VALUES($1,$2,$3,$4,$5,$6) RETURNING id`,
      [filename, total_size, chunk_count, chunk_size, JSON.stringify([]), 'in_progress']
    );
    const upload_id = result.rows[0].id;
    return res.json({ upload_id, chunk_size, chunk_count });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: 'init failed' });
  }
});

// Upload chunk: PUT /api/upload/:upload_id/:chunk_index
router.put('/:upload_id/:chunk_index', async (req, res) => {
  try {
    const { upload_id, chunk_index } = req.params;
    const idx = parseInt(chunk_index, 10);
    if (isNaN(idx)) return res.status(400).json({ error: 'invalid chunk index' });

    // read upload metadata
    const up = await pool.query('SELECT * FROM uploads WHERE id=$1', [upload_id]);
    if (up.rows.length === 0) return res.status(404).json({ error: 'upload not found' });
    const meta = up.rows[0];
    const tmpDir = path.join(UPLOAD_TMP_DIR, upload_id);
    fs.mkdirSync(tmpDir, { recursive: true });

    const chunkPath = path.join(tmpDir, `chunk_${idx}`);
    const writeStream = fs.createWriteStream(chunkPath, { flags: 'w' });
    req.pipe(writeStream);
    await new Promise((resolve, reject) => {
      writeStream.on('finish', resolve);
      writeStream.on('error', reject);
      req.on('error', reject);
    });

    // register uploaded chunk in DB if not present
    const uploaded = new Set(JSON.parse(meta.uploaded_chunks || '[]'));
    uploaded.add(idx);
    await pool.query('UPDATE uploads SET uploaded_chunks=$1, updated_at=now() WHERE id=$2', [JSON.stringify([...uploaded]), upload_id]);

    return res.json({ ok: true, uploaded_chunks_count: uploaded.size });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: 'chunk upload failed' });
  }
});

// Status: GET /api/upload/:upload_id/status
router.get('/:upload_id/status', async (req, res) => {
  try {
    const { upload_id } = req.params;
    const up = await pool.query('SELECT id, filename, total_size, chunk_count, chunk_size, uploaded_chunks, status FROM uploads WHERE id=$1', [upload_id]);
    if (up.rows.length === 0) return res.status(404).json({ error: 'upload not found' });
    return res.json(up.rows[0]);
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: 'status failed' });
  }
});

// Complete upload: POST /api/upload/:upload_id/complete
router.post('/:upload_id/complete', async (req, res) => {
  try {
    const { upload_id } = req.params;
    const up = await pool.query('SELECT * FROM uploads WHERE id=$1', [upload_id]);
    if (up.rows.length === 0) return res.status(404).json({ error: 'upload not found' });
    const meta = up.rows[0];
    const tmpDir = path.join(UPLOAD_TMP_DIR, upload_id);
    const outPath = path.join(UPLOAD_DIR, meta.filename);

    // Verify all chunks present
    const uploaded = new Set(JSON.parse(meta.uploaded_chunks || '[]'));
    if (uploaded.size !== meta.chunk_count) {
      return res.status(400).json({ error: 'not all chunks uploaded', uploaded_count: uploaded.size });
    }

    // Assemble atomically: write to temp file then rename
    const tempOut = outPath + '.part';
    const outStream = fs.createWriteStream(tempOut, { flags: 'w' });
    for (let i = 0; i < meta.chunk_count; i++) {
      const chunkPath = path.join(tmpDir, `chunk_${i}`);
      if (!fs.existsSync(chunkPath)) {
        outStream.close();
        return res.status(500).json({ error: `missing chunk ${i}` });
      }
      const data = fs.readFileSync(chunkPath);
      outStream.write(data);
    }
    outStream.end();
    await new Promise((resolve) => outStream.on('finish', resolve));

    // Compute checksum
    const hash = crypto.createHash('sha256');
    const fileBuffer = fs.readFileSync(tempOut);
    hash.update(fileBuffer);
    const checksum = hash.digest('hex');

    // Move into final place atomically
    fs.renameSync(tempOut, outPath);

    // update DB
    await pool.query('UPDATE uploads SET status=$1, checksum=$2, updated_at=now() WHERE id=$3', ['completed', checksum, upload_id]);

    // cleanup tmp chunks
    fs.rmSync(tmpDir, { recursive: true, force: true });

    return res.json({ ok: true, checksum });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: 'complete failed' });
  }
});

module.exports = router;
