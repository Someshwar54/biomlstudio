// backend/src/middleware/auth.js
const jwt = require('jsonwebtoken');
const JWT_SECRET = process.env.JWT_SECRET || 'devsecret';

function requireAuth(req,res,next){
  const h = req.headers.authorization;
  if(!h) return res.status(401).json({error:'auth required'});
  const token = h.split(' ')[1];
  try { req.user = jwt.verify(token, JWT_SECRET); next(); } catch(e){ return res.status(401).json({error:'invalid token'}); }
}
function requireRole(role){
  return (req,res,next)=>{ if(!req.user) return res.status(401).end(); if(req.user.role!==role) return res.status(403).json({error:'forbidden'}); next(); };
}
module.exports = { requireAuth, requireRole };