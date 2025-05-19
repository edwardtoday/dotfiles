#!/bin/bash

# 脚本：禁用特定子网通过有线网络的路由

echo "disable_wired_subnets.sh called at $(date)" >> /tmp/hspoon_route.log

echo "正在删除有线网络接口的静态路由..."

sudo /sbin/route -n delete -net 192.168.0.0/16
sudo /sbin/route -n delete -net 172.16.0.0/12
sudo /sbin/route -n delete -net 192.169.0.0/16
sudo /sbin/route -n delete -net 192.170.0.0/16

echo "只清理通过 en7 的相关静态路由..."

for prefix in "192.168" "172.16" "192.169" "192.170"; do
    netstat -rn | awk -v pfx="$prefix" '$0 ~ "en7" && $1 ~ "^"pfx {print $1}' | while read route; do
        # 判断是net还是host
        if [[ "$route" =~ / ]]; then
            echo "删除网络 $route via en7"
            sudo /sbin/route -n delete -net "$route"
        else
            echo "删除主机 $route via en7"
            sudo /sbin/route -n delete -host "$route"
        fi
    done
done

echo "静态路由删除完成。"
