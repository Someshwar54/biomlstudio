// backend/src/db/pool.js
const { Pool } = require('pg');

const connectionString = process.env.DATABASE_URL || process.env.DATABASE_URL_LOCAL || 'postgres://bioml_admin:bioml_pass@postgres:5432/biomlstudio';

const pool = new Pool({
  connectionString,
});

module.exports = pool;
