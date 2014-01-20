#!/bin/sh
## Script to backup Thunderbird mail
set -x
x=`date +%y%m%d.%H%M`
XZ_OPT=-6 tar cJf /tmp/thunderbird-${x}.tar.xz /home/qingpei/.thunderbird
mv /tmp/thunderbird-${x}.tar.xz /home/qingpei/Dropbox/Workspace/Sansi/backup/

