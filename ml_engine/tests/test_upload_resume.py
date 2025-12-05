import os, subprocess, time, requests, hashlib

BASE='http://localhost:4000/api/upload'
SAMPLE='data/sample/test_resume.bin'


def ensure_sample():
    os.makedirs('data/sample', exist_ok=True)
    if not os.path.exists(SAMPLE) or os.path.getsize(SAMPLE) < 1024*1024:
        with open(SAMPLE,'wb') as f:
            f.write(os.urandom(2*1024*1024))  # 2MB
    h=hashlib.sha256()
    with open(SAMPLE,'rb') as f:
        while True:
            b=f.read(65536)
            if not b: break
            h.update(b)
    return h.hexdigest()


def wait_server_ready(url='http://localhost:4000/healthz', timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.2)
    return False


def test_resume_upload():
    checksum = ensure_sample()

    # start backend server
    proc = subprocess.Popen(['node', 'backend/src/server.js'], cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        assert wait_server_ready(), 'Backend did not start'

        total = os.path.getsize(SAMPLE)
        chunk_size = 1024*1024
        filename = os.path.basename(SAMPLE)

        # init
        r = requests.post(f"{BASE}/init", json={'filename': filename, 'total_size': total, 'chunk_size': chunk_size})
        r.raise_for_status()
        data = r.json()
        upload_id = data['upload_id']
        chunk_count = data['chunk_count']

        # upload first half
        half = chunk_count // 2
        with open(SAMPLE, 'rb') as f:
            for idx in range(half):
                f.seek(idx * chunk_size)
                chunk = f.read(chunk_size)
                r = requests.put(f"{BASE}/{upload_id}/{idx}", data=chunk)
                r.raise_for_status()

        # check status
        st = requests.get(f"{BASE}/{upload_id}/status").json()
        uploaded = st.get('uploaded_chunks') or []
        assert len(uploaded) == half

        # resume upload remaining
        with open(SAMPLE, 'rb') as f:
            for idx in range(half, chunk_count):
                f.seek(idx * chunk_size)
                chunk = f.read(chunk_size)
                r = requests.put(f"{BASE}/{upload_id}/{idx}", data=chunk)
                r.raise_for_status()

        # complete
        res = requests.post(f"{BASE}/{upload_id}/complete")
        res.raise_for_status()
        body = res.json()
        assert body.get('checksum') is not None
        assert body['checksum'] == checksum

        # verify tmp dir cleaned
        tmpdir = os.path.join('data','uploads','tmp', upload_id)
        assert not os.path.exists(tmpdir)

    finally:
        proc.terminate()
        proc.wait(timeout=5)

