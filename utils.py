import os.path
import time
import json
import redis


def get_redis(name, key, value):
    re = redis.Redis(host='localhost', port=6379, db=0)
    return re


def log(*args, **kwargs):
    # time.time() 返回 unix time
    # 如何把 unix time 转换为普通人类可以看懂的格式呢？
    format = '%Y-%m-%d %H:%M:%S'
    value = time.localtime(int(time.time()))
    dt = time.strftime(format, value)
    with open('gua.log.txt', 'a', encoding='utf-8') as f:
        print(dt, *args, file=f, **kwargs)


def format_time(models):
    format_cts = {}
    if not hasattr(models, '__iter__'):
        models = [models]

    for model in models:
        format_cts[model.id]  = {
            'ct': change_time(model.created_time),
            'ut': change_time(model.updated_time),
        }

    return format_cts


def change_time(_time):
    time_format = '%Y/%m/%d'
    localtime = time.localtime(_time)
    return time.strftime(time_format, localtime)


import redis, random

squ = 'qwertyuiopasdfghjklzxcvbnm1234567890'
key = 'fuck'
re = redis.Redis(host='localhost', port=6379, db=0)

for i in range(200):
    codes = []
    for j in range(5):
        code = ''.join(random.sample(str.upper(squ), 5))
        codes.append(code)
    re.hset(key, 'code', '-'.join(codes))

print(re.hget(key, 'code'))
#只打印了50个
# for c in re.hget(key, 'code', 0, 50):
#     print(c)