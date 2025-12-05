# tests: register, login, request xai, run worker, fetch result
import requests, time, os, subprocess
BASE='http://localhost:4000'
def test_flow():
    # register
    r = requests.post(BASE+'/api/auth/register', json={'username':'u1','password':'p1'})
    assert r.status_code==200
    r = requests.post(BASE+'/api/auth/login', json={'username':'u1','password':'p1'})
    token = r.json()['token']
    h = {'Authorization':f'Bearer {token}'}
    r2 = requests.post(BASE+'/api/xai/request', headers=h, json={'job_id':None,'model_path':None,'sample':[0,1,2]})
    assert r2.status_code==200
    xai_id = r2.json()['xai_id']
    # start worker manually in separate terminal before running this test; here we poll for result
    for _ in range(30):
        r3 = requests.get(BASE+f'/api/xai/{xai_id}', headers=h)
        if r3.status_code==200 and r3.headers.get('content-type','').startswith('application/json'):
            return
        time.sleep(1)
    assert False, "XAI result not ready"