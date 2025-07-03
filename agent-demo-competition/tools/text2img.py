#!/usr/bin/env python
# encoding: utf-8

import requests
import json
from tools.auth_util import gen_sign_headers
import time


def submit(prompt,app_id = '2025761464',app_key = 'uTfCZSgrEjvqauix',uri = '/api/v1/task_submit',domain = 'api-ai.vivo.com.cn',method = 'POST'):
   params = {}
   data = {
    'height': 400,
    'width': 400,
    'prompt': prompt,
    'styleConfig': '7a0079b5571d5087825e52e26fc3518b',
    'userAccount': 'thisistestuseraccount'
   }

   headers = gen_sign_headers(app_id, app_key, method, uri, params)
   headers['Content-Type'] = 'application/json'

   url = 'http://{}{}'.format(domain, uri)
   response = requests.post(url, data=json.dumps(data), headers=headers)
   if response.status_code == 200:
       response = response.json()
       img_id = response['result']["task_id"]
       return img_id
   else:
       print(response.status_code, response.text)


def progress(img_id,app_id = '2025761464',app_key = 'uTfCZSgrEjvqauix',uri = '/api/v1/task_progress',domain = 'api-ai.vivo.com.cn',method = 'GET'):
    params = {
        # 注意替换为提交作画任务时返回的task_id
        'task_id': img_id
    }
    headers = gen_sign_headers(app_id, app_key, method, uri, params)

    uri_params = ''
    for key, value in params.items():
        uri_params = uri_params + key + '=' + value + '&'
    uri_params = uri_params[:-1]

    url = 'http://{}{}?{}'.format(domain, uri, uri_params)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response = response.json()
        if 'images_url' in response['result'] and len(response['result']['images_url']) > 0:
            img_url = response['result']['images_url'][0]
        else:
            time.sleep(0.5)
            img_id = response['result']['task_id']
            img_url = progress(img_id)
        return img_url
    else:
        print(response.status_code, response.text)


def text_to_img(prompt):
    img_id = submit(prompt)
    time.sleep(0)
    img_url = progress(img_id)
    return img_url



if __name__ == '__main__':
    img_url = text_to_img("your pronunciation is good enough but the content is not clear")

    print(img_url)
