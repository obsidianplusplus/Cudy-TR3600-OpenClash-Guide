#!/bin/sh
# Read-only device checks / 只读检查，不安装、不修改配置。
set -eu
expected='6.12.93~f67f61bf2367ca6002566e9da365b1b8-r1'
board="$(ubus call system board | jsonfilter -e '@.board_name')"
[ "$board" = 'cudy,tr3600-v1' ] || { echo 'STOP: board mismatch / 设备型号不匹配'; exit 1; }
[ "$(uname -r)" = '6.12.93' ] || { echo 'STOP: kernel mismatch / 内核版本不匹配'; exit 1; }
apk info -v kernel | grep -Fq "$expected" || { echo 'STOP: kernel ABI mismatch / 内核 ABI 不匹配'; exit 1; }
[ "$(apk --print-arch)" = 'aarch64_cortex-a53' ] || { echo 'STOP: architecture mismatch / 架构不匹配'; exit 1; }
echo 'Device + kernel checks PASS / 设备与内核检查通过'
echo 'LAN addresses / LAN 地址:'
uci get network.lan.ipaddr
echo 'IPv4 routes / IPv4 路由:'
ip -4 route
echo 'Flash space / 闪存空间:'
df -Pk /overlay
echo 'Memory / 内存:'
free
echo 'Next: inspect LAN/WAN overlap and copy a private backup to your computer.'
echo '下一步：检查 LAN/WAN 是否重叠，将私人备份复制到电脑后再安装。'
