#!/bin/sh
## Script to backup Thunderbird mail
set -x
x=`date +%y%m%d.%H%M`
cd /home/qingpei
XZ_OPT=-6 tar cJf /tmp/thunderbird-${x}.tar.xz .thunderbird
mv /tmp/thunderbird-${x}.tar.xz /home/qingpei/Dropbox/Workspace/Sansi/backup/
cd /home/qingpei/Dropbox/Workspace/Sansi/backup
# keep only last 5 backups
(ls -t | head -n 5;ls) | sort | uniq -u | xargs rm

