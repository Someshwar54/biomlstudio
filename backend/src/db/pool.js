// backend/src/db/pool.js
const { Pool } = require('pg');

// default to localhost for dev runs where Postgres is exposed on the host
const connectionString = process.env.DATABASE_URL || process.env.DATABASE_URL_LOCAL || 'postgres://bioml_admin:bioml_pass@localhost:5432/biomlstudio';

const pool = new Pool({
  connectionString,
});

module.exports = pool;
