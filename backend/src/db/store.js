const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const pool = require('./pool');

// File-based fallback store used when Postgres isn't reachable. This makes running
// the backend (and the upload resume test) possible without Docker/Postgres.
const META_FILE = path.resolve(process.cwd(), 'data', 'uploads', 'uploads_meta.json');
fs.mkdirSync(path.dirname(META_FILE), { recursive: true });

function _readAll() {
  try {
    if (!fs.existsSync(META_FILE)) return {};
    const raw = fs.readFileSync(META_FILE, 'utf8');
    return JSON.parse(raw || '{}');
  } catch (err) {
    console.error('failed read meta file', err);
    return {};
  }
}

function _writeAll(obj) {
  try {
    fs.writeFileSync(META_FILE, JSON.stringify(obj, null, 2), 'utf8');
  } catch (err) {
    console.error('failed write meta file', err);
    throw err;
  }
}

async function _dbAvailable() {
  if (!pool || !pool.query) return false;
  try {
    await pool.query('SELECT 1');
    return true;
  } catch (err) {
    return false;
  }
}

async function createUpload({ filename, total_size, chunk_size }) {
  const chunk_count = Math.ceil(total_size / chunk_size);

  if (await _dbAvailable()) {
    const res = await pool.query(
      `INSERT INTO uploads(filename, total_size, chunk_count, chunk_size, uploaded_chunks, status)
       VALUES($1,$2,$3,$4,$5,$6) RETURNING id, chunk_count`,
      [filename, total_size, chunk_count, chunk_size, JSON.stringify([]), 'in_progress']
    );
    return { id: res.rows[0].id, chunk_count: res.rows[0].chunk_count };
  }

  // fallback to file-based store
  const id = crypto.randomUUID ? crypto.randomUUID() : crypto.randomBytes(16).toString('hex');
  const now = new Date().toISOString();
  const record = {
    id,
    filename,
    total_size,
    chunk_count,
    chunk_size,
    uploaded_chunks: [],
    status: 'in_progress',
    checksum: null,
    created_at: now,
    updated_at: now,
  };
  const all = _readAll();
  all[id] = record;
  _writeAll(all);
  return { id, chunk_count };
}

async function getUpload(id) {
  if (await _dbAvailable()) {
    const res = await pool.query('SELECT * FROM uploads WHERE id=$1', [id]);
    if (res.rows.length === 0) return null;
    return res.rows[0];
  }

  const all = _readAll();
  return all[id] || null;
}

async function updateUploadedChunks(id, uploadedArray) {
  if (await _dbAvailable()) {
    const json = JSON.stringify(uploadedArray);
    await pool.query('UPDATE uploads SET uploaded_chunks=$1, updated_at=now() WHERE id=$2', [json, id]);
    return;
  }
  const all = _readAll();
  const r = all[id];
  if (!r) throw new Error('upload not found');
  r.uploaded_chunks = uploadedArray;
  r.updated_at = new Date().toISOString();
  all[id] = r;
  _writeAll(all);
}

async function updateStatusAndChecksum(id, status, checksum) {
  if (await _dbAvailable()) {
    await pool.query('UPDATE uploads SET status=$1, checksum=$2, updated_at=now() WHERE id=$3', [status, checksum, id]);
    return;
  }
  const all = _readAll();
  const r = all[id];
  if (!r) throw new Error('upload not found');
  r.status = status;
  r.checksum = checksum;
  r.updated_at = new Date().toISOString();
  all[id] = r;
  _writeAll(all);
}

module.exports = {
  createUpload,
  getUpload,
  updateUploadedChunks,
  updateStatusAndChecksum,
  _dbAvailable,
};
