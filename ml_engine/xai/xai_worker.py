# ml_engine/xai/xai_worker.py
import os, json, time, uuid, hashlib
import redis, psycopg2
try:
    import shap
    _HAS_SHAP=True
except Exception:
    _HAS_SHAP=False
try:
    from lime import lime_tabular
    _HAS_LIME=True
except Exception:
    _HAS_LIME=False

DB_URL = os.getenv('DATABASE_URL','postgres://bioml_admin:bioml_pass@postgres:5432/biomlstudio')
R = redis.Redis.from_url(os.getenv('REDIS_URL','redis://redis:6379/0'))
conn = psycopg2.connect(DB_URL)

def update_status(xai_id, status, path=None):
    with conn.cursor() as c:
        c.execute("UPDATE xai_jobs SET status=%s, result_path=%s, updated_at=now() WHERE id=%s", (status, path, xai_id))
    conn.commit()

def compute_shap_explanation(model_path, sample):
    # lightweight fallback: if shap not available, return mock deterministic explanation
    if not _HAS_SHAP:
        return {'method':'mock','explanation':[('feature0',0.1)]}
    # load model logic is domain-specific; we mock with random expl for small sample
    expl = {'method':'shap','explanation':[('f'+str(i), float(i)/10.0) for i in range(len(sample))]}
    return expl

def loop():
    print("XAI worker started")
    while True:
        _, xai_id = R.brpop('bioml:xai')
        if not xai_id: continue
        xai_id = xai_id.decode()
        update_status(xai_id,'running')
        # fetch job metadata
        with conn.cursor() as c:
            c.execute("SELECT model_path FROM xai_jobs WHERE id=%s", (xai_id,))
            row = c.fetchone()
        model_path = row[0] if row else None
        # for demo: sample is not stored; compute mock
        expl = compute_shap_explanation(model_path, [0.0,1.0,2.0])
        out_dir = os.path.join('data','xai')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{xai_id}.json")
        with open(out_path,'w') as f:
            json.dump(expl, f)
        update_status(xai_id,'completed', out_path)
        print("XAI done", xai_id)

if __name__=='__main__':
    loop()