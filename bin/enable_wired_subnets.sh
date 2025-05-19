#!/bin/bash

GW_IP="192.168.233.1" # 你en7的网关

# 先清理
sudo route -n delete -net 192.168.0.0/16
sudo route -n delete -net 172.16.0.0/12
sudo route -n delete -net 192.169.0.0/16
sudo route -n delete -net 192.170.0.0/16

# 再添加通过网关的路由
sudo route -n add -net 192.168.0.0/16 $GW_IP
sudo route -n add -net 172.16.0.0/12 $GW_IP
sudo route -n add -net 192.169.0.0/16 $GW_IP
sudo route -n add -net 192.170.0.0/16 $GW_IP

echo "已通过网关 $GW_IP 强制路由到有线 en7"
netstat -nr | grep -E "192.168|172.16|192.169|192.170"
