// backend/src/routes/auth.js
const express = require('express');
const pool = require('../db/pool');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const router = express.Router();
const JWT_SECRET = process.env.JWT_SECRET || 'devsecret';

router.post('/register', async (req,res)=>{
  const {username,password,role} = req.body;
  if(!username||!password) return res.status(400).json({error:'missing'});
  const hash = await bcrypt.hash(password, 10);
  const q = await pool.query('INSERT INTO users(username,password_hash,role) VALUES($1,$2,$3) RETURNING id,username,role',[username,hash,role||'user']);
  const u=q.rows[0];
  res.json({id:u.id,username:u.username,role:u.role});
});

router.post('/login', async (req,res)=>{
  const {username,password} = req.body;
  const q = await pool.query('SELECT id, password_hash, role FROM users WHERE username=$1',[username]);
  if(q.rows.length===0) return res.status(401).json({error:'invalid'});
  const u=q.rows[0];
  const ok = await bcrypt.compare(password, u.password_hash);
  if(!ok) return res.status(401).json({error:'invalid'});
  const token = jwt.sign({sub:u.id,role:u.role,username}, JWT_SECRET, {expiresIn:'8h'});
  res.json({token});
});

module.exports = router;