const express = require('express');
require('dotenv').config();
const app = express();
app.use(express.json());

// register upload routes
app.use('/api/upload', require('./routes/upload'));

// register jobs routes (producer for job queue)
app.use('/api/jobs', require('./routes/jobs'));

// register auth routes
app.use('/api/auth', require('./routes/auth'));

// register xai routes
app.use('/api/xai', require('./routes/xai'));

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
	const migrationDir = path.resolve(process.cwd(), 'infrastructure', 'db', 'migrations');
	if (!fs.existsSync(migrationDir)) {
		console.log('No migration directory found at', migrationDir);
		return;
	}

	// Apply all migrations in order (001, 002, etc.)
	const migrations = fs.readdirSync(migrationDir)
		.filter(f => f.endsWith('.sql'))
		.sort();
	
	for (const migFile of migrations) {
		const sqlPath = path.join(migrationDir, migFile);
		try {
			const sql = fs.readFileSync(sqlPath, 'utf8');
			console.log(`[migrations] applying ${migFile}...`);
			await pool.query(sql);
			console.log(`[migrations] ${migFile} applied (idempotent).`);
		} catch (err) {
			console.error(`[migrations] failed to apply ${migFile}:`, err.message);
		}
	}
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
