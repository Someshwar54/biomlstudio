const express = require('express');
require('dotenv').config();
const app = express();
app.use(express.json());

// register upload routes
app.use('/api/upload', require('./routes/upload'));

// Health check endpoint (lightweight for docker healthchecks)
app.get('/healthz', (req, res) => res.status(200).json({status:'ok'}));

// Main endpoint
app.get('/', (req, res) => res.send('BioMLStudio Backend stub'));

const fs = require('fs');
const path = require('path');
const PORT = process.env.PORT || 4000;

// Attempt to apply DB migrations at start-up if available. This makes local dev/tests
// resilient: if the uploads table doesn't exist we'll run the SQL migration file.
async function ensureMigrations(pool) {
	const sqlPath = path.resolve(process.cwd(), 'infrastructure', 'db', 'migrations', '001_create_uploads.sql');
	if (!fs.existsSync(sqlPath)) {
		console.log('No migration file found at', sqlPath);
		return;
	}

	const sql = fs.readFileSync(sqlPath, 'utf8');
	console.log('Applying DB migration:', sqlPath);
	await pool.query(sql);
	console.log('DB migration applied (if needed).');
}

async function bootstrap() {
	// require the pool lazily so environment variables read correctly
	const pool = require('./db/pool');

	// Try a few times to apply migrations - Postgres in Docker may still be starting
	let attempts = 0;
	const maxAttempts = 10;
	while (attempts < maxAttempts) {
		try {
			await ensureMigrations(pool);
			break;
		} catch (err) {
			attempts += 1;
			console.log(`DB unavailable yet (attempt ${attempts}/${maxAttempts}). Retrying in 1s...`);
			await new Promise((r) => setTimeout(r, 1000));
		}
	}

	app.listen(PORT, () => console.log(`Backend running on ${PORT}`));
}

bootstrap();
