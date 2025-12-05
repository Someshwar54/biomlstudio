#!/usr/bin/env python3
import requests, os, sys, time, hashlib, json
BASE = os.environ.get('API_URL', 'http://localhost:4000/api/upload')


def create_sample(path, size_mb=10):
    with open(path, 'wb') as f:
        f.write(os.urandom(size_mb * 1024 * 1024))
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(65536)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def init_upload(filename, total, chunk_size):
    r = requests.post(f"{BASE}/init", json={'filename': filename, 'total_size': total, 'chunk_size': chunk_size})
    r.raise_for_status()
    return r.json()


def status(upload_id):
    r = requests.get(f"{BASE}/{upload_id}/status")
    r.raise_for_status()
    return r.json()


def upload_chunk(upload_id, idx, data):
    r = requests.put(f"{BASE}/{upload_id}/{idx}", data=data, headers={'Content-Type':'application/octet-stream'})
    r.raise_for_status()
    return r.json()


def complete_upload(upload_id):
    r = requests.post(f"{BASE}/{upload_id}/complete")
    r.raise_for_status()
    return r.json()


def upload_file(path, chunk_size=1*1024*1024, resume_upload_id=None, interrupt_after=None):
    total = os.path.getsize(path)
    filename = os.path.basename(path)

    if resume_upload_id:
        upload_id = resume_upload_id
        st = status(upload_id)
        uploaded = set(st.get('uploaded_chunks') or [])
        chunk_count = st['chunk_count']
        print(f"Resuming upload {upload_id} - already have {len(uploaded)}/{chunk_count} chunks")
    else:
        resp = init_upload(filename, total, chunk_size)
        upload_id = resp['upload_id']
        chunk_count = resp['chunk_count']
        uploaded = set()
        print(f"New upload {upload_id} chunk_count={chunk_count}")

    with open(path, 'rb') as f:
        for idx in range(chunk_count):
            if idx in uploaded:
                print(f"Skipping already uploaded chunk {idx}")
                continue
            if interrupt_after is not None and idx == interrupt_after:
                print("Simulating interruption at chunk", idx)
                break
            f.seek(idx * chunk_size)
            chunk = f.read(chunk_size)
            upload_chunk(upload_id, idx, chunk)
            print("Uploaded", idx)
    return upload_id


if __name__ == '__main__':
    sample = 'data/sample/large.bin'
    os.makedirs('data/sample', exist_ok=True)
    if not os.path.exists(sample):
        print("Creating sample...")
        checksum = create_sample(sample, size_mb=5)  # 5MB test file
        print("checksum", checksum)
    else:
        import hashlib
        h = hashlib.sha256()
        with open(sample,'rb') as f:
            while True:
                b = f.read(65536)
                if not b: break
                h.update(b)
        checksum = h.hexdigest()

    # Demonstration: create, upload first 2 chunks, then resume and finish
    uid = upload_file(sample, chunk_size=1024*1024, resume_upload_id=None, interrupt_after=2)
    print('Interrupted upload id:', uid)

    # resume existing
    uid2 = upload_file(sample, chunk_size=1024*1024, resume_upload_id=uid, interrupt_after=None)
    print('Resumed and finished upload id:', uid2)

    res = complete_upload(uid2)
    print('Complete response:', res)
    print('Uploaded file checksum (local):', checksum)
