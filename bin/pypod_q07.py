#!/usr/bin/env python
#-*- coding:utf-8 -*-

import httplib, urllib
import socket
import time

# 替换上你的Email，密码，域名ID，记录ID等参数，就可以运行了。
# 会在后台一直运行，每隔30秒检查一遍IP，如果修改了就更新IP。

# 获得domain_id可以用curl
# curl -k https://dnsapi.cn/Domain.List -d "login_email=xxx&login_password=xxx"

# 获得record_id类似
# curl -k https://dnsapi.cn/Record.List -d "login_email=xxx&login_password=xxx&domain_id=xxx"

params = dict(
    login_email="edwardtoday@gmail.com", # replace with your email
    login_password="et@dnspod", # replace with your password
    format="json",
    domain_id=1781648, # replace with your domain_od, can get it by API Domain.List
    record_id=13206427, # replace with your record_id, can get it by API Record.List
    sub_domain="q07", # replace with your sub_domain
    record_line="默认",
)
current_ip = None

def ddns(ip):
    params.update(dict(value=ip))
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/json"}
    conn = httplib.HTTPSConnection("dnsapi.cn")
    conn.request("POST", "/Record.Ddns", urllib.urlencode(params), headers)

    response = conn.getresponse()
    print response.status, response.reason
    data = response.read()
    print data
    conn.close()
    return response.status == 200

def getip():
    sock = socket.create_connection(('ns1.dnspod.net', 6666))
    ip = sock.recv(16)
    sock.close()
    return ip

if __name__ == '__main__':
    try:
        ip = getip()
        print ip
        if current_ip != ip:
            if ddns(ip):
                current_ip = ip
    except Exception, e:
        print e
        pass
