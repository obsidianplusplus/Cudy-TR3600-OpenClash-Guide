#!/bin/sh
# Usage: sh rollback_guard.sh arm /tmp/oc-before 900
#        sh rollback_guard.sh confirm /tmp/oc-before
# Manual recovery: sh rollback_guard.sh restore /tmp/oc-before
# Snapshot directory must already contain dhcp.conf + firewall.conf.
set -eu
action="${1:?arm|confirm|restore}"
dir="${2:?snapshot-directory}"
lock_decision() {
    mkdir "$dir/decision.lock" || { echo 'Decision in progress / 正在确认或回退，请先检查状态'; exit 1; }
    trap 'rmdir "$dir/decision.lock" 2>/dev/null || true' EXIT
}
restore() {
    uci set openclash.config.enable='0'
    uci commit openclash
    /etc/init.d/openclash stop || true
    cp "$dir/dhcp.conf" /etc/config/dhcp
    cp "$dir/firewall.conf" /etc/config/firewall
    /etc/init.d/firewall restart
    /etc/init.d/dnsmasq restart
    /etc/init.d/adblock-fast restart || true
    touch "$dir/restored"
}
case "$action" in
    arm)
        test -s "$dir/dhcp.conf" && test -s "$dir/firewall.conf"
        test ! -e "$dir/confirmed" && test ! -e "$dir/restored"
        delay="${3:-900}"
        case "$delay" in ''|*[!0-9]*) echo 'Invalid timeout'; exit 1;; esac
        echo "Rollback armed for ${delay}s / 回退计时已启动"
        sleep "$delay"
        lock_decision
        test ! -e "$dir/confirmed" || exit 0
        restore
        ;;
    confirm)
        lock_decision
        test ! -e "$dir/restored" || { echo 'Already restored; do not confirm / 已回退，请重新验证'; exit 1; }
        touch "$dir/confirmed"
        echo 'Confirmed / 已确认保留当前配置'
        ;;
    restore) lock_decision; restore ;;
    *) exit 1 ;;
esac
