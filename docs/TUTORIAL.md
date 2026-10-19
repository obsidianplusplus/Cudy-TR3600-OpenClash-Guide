# 完整操作教程 / Complete installation tutorial

[返回首页 / Back to README](../README.md)

## 1. 这次到底升级了什么 / What was upgraded

中文：本次“升级”是插件和功能升级：在保留原固件、原 Linux 内核和无线驱动的前提下安装官方 OpenClash。最终运行 Fake-IP 混合模式，TCP 使用重定向、UDP 使用 TUN，网络栈为 gVisor。没有执行刷机、恢复出厂或替换现有防火墙内核模块。

English: This was a feature and package upgrade on the existing firmware. Official OpenClash runs in Fake-IP mixed mode, using TCP redirection and UDP through a gVisor TUN. Firmware, running kernel and wireless drivers were retained; no factory reset or replacement of existing firewall modules was performed.

中文：本教程有两条路线。完全符合首页兼容表的设备可使用本次适配包；其他内核必须先阅读 [编译章节](KERNEL-BUILD.md)。不要通过忽略 kernel 依赖、修改版本字符串或强制加载不兼容 `.ko` 来代替适配。

English: There are two routes. Devices matching the compatibility table can use these artifacts. Other kernels require the [build procedure](KERNEL-BUILD.md). Ignoring a kernel dependency, editing a version string or forcing an incompatible `.ko` is not a substitute for adaptation.

## 2. 先理解网络 / Understand the network first

```text
Modem / 光猫: 192.168.1.1/24
    |
TR3600 WAN: eth0, DHCP, tested address 192.168.1.5
TR3600 LAN: br-lan, 192.168.10.1/24
    +-- eth1 -> switch / 交换机 -> computers / 电脑
    +-- Cudy-2.4G
    +-- Cudy-5G
    +-- Cudy-MLO
```

中文：本次设备由光猫负责上游联网，OpenWrt WAN 自动获取地址。LAN 是另一个网段；下游电脑使用 OpenWrt 的 DHCP，地址池为 `192.168.10.100` 至 `192.168.10.249`，掩码 `255.255.255.0`，网关与 DNS 均为 `192.168.10.1`。WAN 的具体租约可能变化，无需固定为 `.5`。

English: The modem supplies upstream connectivity and a DHCP lease to the OpenWrt WAN. LAN is a separate subnet. Downstream clients use OpenWrt DHCP: `192.168.10.100`–`192.168.10.249`, mask `255.255.255.0`, gateway and DNS `192.168.10.1`. The WAN lease can change; `.5` is an observation, not a required setting.

中文：普通交换机仅扩展 LAN 端口，无需拨号或另开 DHCP。交换机只接一条来自 TR3600 LAN 的上联。避免把光猫 LAN 或其他路由器的 LAN 另外接到这个下游交换机上。

English: An ordinary Ethernet switch extends the LAN and requires no PPPoE or additional DHCP service. Use one uplink from TR3600 LAN. Avoid an additional uplink from the modem or another router's LAN into this downstream switch.

## 3. 后台丢失的起因与恢复 / Recovering the lost management page

中文：最初删除了 `192.168.1.1/24`，只留下没有前缀的 `192.168.10.1`。实机检查发现 LAN 成了 `/32`，所以仅给电脑设置 `192.168.10.2/24` 并不足以保证双向通信。修复点是把路由器 LAN 正确设为 `192.168.10.1/24`。

English: The original change removed `192.168.1.1/24` and left a bare `192.168.10.1`. On this device the resulting LAN address had a `/32` prefix. Assigning `192.168.10.2/24` to the computer did not fix the router's return-path configuration. The necessary correction was `192.168.10.1/24` on LAN.

**电脑 / Computer, macOS — read-only diagnostics:**

```sh
networksetup -listallhardwareports
networksetup -getinfo Wi-Fi
route -n get 192.168.10.1
arp -an
ndp -an
```

中文：不要假设 `en0` 一定是 Wi-Fi。本次 Mac 的 `en0` 是以太网、`en1` 是 Wi-Fi；VPN 还会创建 `utun` 接口。先确认路由和实际接口，才能解释测试结果。LuCI 也可能自动回滚网络变更，所以原、新地址都应检查。

English: Do not assume `en0` is Wi-Fi. Here `en0` was Ethernet and `en1` Wi-Fi, with additional VPN `utun` interfaces. Identify the route and interface before interpreting tests. LuCI may roll back an unconfirmed network change, so check both old and new addresses.

中文：本次通过仍可达的 IPv6 管理链路和本地转发进入 LuCI，保留配置后修正 LAN。若已经知道路由器的可达链路本地 IPv6，并且 SSH 可用，可用下列替代方式建立只监听本机的转发。将占位符换成实际地址和接口；它不是自动发现命令。

English: Recovery used the still-reachable IPv6 management path and a local relay to LuCI. If a reachable link-local IPv6 address is already known and SSH works, the following alternative provides a localhost-only tunnel. Replace the placeholders; this command does not discover the address.

```sh
# Computer / 电脑; replace ROUTER_ADDRESS and WIFI_INTERFACE first.
ssh -N -L 127.0.0.1:18080:127.0.0.1:80 \
  'root@fe80::ROUTER_ADDRESS%WIFI_INTERFACE'
# Then open / 然后打开: http://127.0.0.1:18080/
```

中文：进入 LuCI 后，在“网络 → 接口 → LAN → 编辑”将 IPv4 地址写成 `192.168.10.1/24`，保存并按页面提示确认。若 SSH 已可用，也可在确认接口名称为 `lan` 后执行下面的修复。网络重载可能短暂断线，重新获取电脑地址后访问新地址。

English: In LuCI, open Network → Interfaces → LAN → Edit and set `192.168.10.1/24`, then apply and confirm as instructed. If SSH is available and the interface is indeed named `lan`, the following performs the same repair. A network reload can briefly interrupt connectivity; renew the client address and reconnect.

```sh
# Router / 路由器
cp -p /etc/config/network /tmp/network-before-lan-fix.conf
uci -q delete network.lan.netmask || true
uci -q delete network.lan.ipaddr || true
uci add_list network.lan.ipaddr='192.168.10.1/24'
uci commit network
ubus call network reload
```

中文：这是当前设备的 CIDR 写法，不是所有旧版 OpenWrt 的通用迁移命令。恢复后访问 `http://192.168.10.1/`。如果 IPv4、IPv6 和 SSH 均不可达，需要另查该型号的有线恢复方式；本次没有执行 Failsafe 或刷机。

English: This uses the CIDR representation of the tested firmware, not a universal migration command for older OpenWrt releases. Reconnect at `http://192.168.10.1/`. If neither IP family nor SSH is reachable, investigate the board's wired recovery procedure separately. Failsafe and flashing were not used in this case.

## 4. 固定版本与兼容检查 / Pin versions and check compatibility

中文：本次软件包管理器是 APK，不是 OPKG。先运行只读检查脚本；完整 kernel 包版本必须与首页一致。还要核对空闲闪存和内存。本次 overlay 约 128 MiB，Mihomo 解压后约 55 MiB，安装成功后仍有约 65 MiB 可用，但其他设备的软件包占用可能不同。

English: The tested firmware uses APK rather than OPKG. Run the read-only preflight script and verify the entire kernel package version. Check flash and RAM as well. The tested overlay was roughly 128 MiB; the decompressed Mihomo core was roughly 55 MiB, leaving approximately 65 MiB after installation. Other package sets change this budget.

```sh
# Computer / 电脑
scp -O scripts/preflight.sh root@192.168.10.1:/tmp/tr3600-preflight.sh
ssh root@192.168.10.1 'sh /tmp/tr3600-preflight.sh'
```

中文：`scp -O` 使用传统 SCP 传输，适合没有 SFTP 服务的精简 OpenWrt。输入自己的管理员密码。不要把口令写进脚本、Git 提交或截图。检查失败时先停止，不要修改脚本以跳过错误。

English: `scp -O` uses legacy SCP transport for minimal OpenWrt systems without SFTP. Enter your own administrator password interactively. Keep credentials out of scripts, commits and screenshots. A failed check should be investigated rather than bypassed.

## 5. 备份与恢复点 / Backups and recovery points

**路由器 / Router, before changing packages:**

```sh
umask 077
sysupgrade -b /tmp/TR3600-before-openclash.tar.gz
mkdir -p /tmp/oc-before
cp -p /etc/config/dhcp /tmp/oc-before/dhcp.conf
cp -p /etc/config/firewall /tmp/oc-before/firewall.conf
cp -p /etc/config/network /tmp/oc-before/network.conf
cp -p /etc/config/wireless /tmp/oc-before/wireless.conf
apk info -v > /tmp/oc-before/packages.txt
sha256sum /etc/config/network /etc/config/wireless > /tmp/oc-before/network-wireless.sha256
```

**电脑 / Computer:**

```sh
mkdir -p private/backups
chmod 700 private private/backups
scp -O root@192.168.10.1:/tmp/TR3600-before-openclash.tar.gz private/backups/
scp -O -r root@192.168.10.1:/tmp/oc-before private/backups/
chmod -R go-rwx private/backups
```

中文：`sysupgrade -b` 备份配置，不会自动备份每个插件二进制或完整闪存。需要可恢复的 OpenClash 运行副本时，还应另存 `/etc/openclash` 和软件包清单。备份可能包含 Wi-Fi 口令、管理员认证和订阅，必须留在私人存储。`/tmp` 重启会丢失，因此必须复制到电脑。

English: `sysupgrade -b` backs up configuration, not every executable or the complete flash. A restorable OpenClash working copy also needs `/etc/openclash` and a package inventory. Backups can contain wireless credentials, administrator authentication and subscriptions. Keep them private and copy them off the router because `/tmp` is volatile.

## 6. 准备安装文件 / Prepare the installation files

中文：在仓库根目录运行下载脚本，得到四个固定版本文件。两个适配 APK 来自本仓库 Release；OpenClash 和 Mihomo 来自各自官方 Release。脚本逐个核对 SHA256，失败则不会把临时文件当成有效下载。

English: Run the downloader from the repository root. It retrieves two adapted APKs from this repository's release and official OpenClash/Mihomo from their upstream releases. Every download is SHA256-verified before being accepted.

```sh
# Computer / 电脑
python3 scripts/fetch_assets.py
scp -O packages/kmod-tun-6.12.93-r100.apk \
  packages/libnetfilter-conntrack3-1.1.0-r100.apk \
  packages/luci-app-openclash-0.48.002.apk \
  packages/mihomo-linux-arm64-v1.19.32.gz \
  root@192.168.10.1:/tmp/
```

中文：需要离线重装时，除了这四个文件还要保存 APK 求解出的全部依赖。本教程不会把“有这四个文件”误称为完整离线依赖仓库。使用当前软件源前，确认它属于同一固件系列；不要把其他发行版的内核包混进来。

English: A fully offline reinstall also requires every dependency resolved by APK. These four assets alone are not an offline package repository. Check that configured feeds belong to the correct firmware family; do not mix in kernel packages from a different build.

## 7. 为什么要适配两个 APK / Why two packages were adapted

中文：OpenClash 是插件，但透明代理依赖内核网络能力。原厂定制快照缺少可直接安装的匹配 TUN 包；仅降级 LuCI 插件不会产生这个内核驱动。我们重建配置并编译了真正的 `tun.ko`，以精确 kernel 依赖打包，设备实际加载和 UDP 测试均通过。

English: OpenClash is an application, but transparent proxying relies on kernel facilities. The vendor snapshot lacked a readily installable matching TUN package. Downgrading LuCI cannot create the missing driver. A real `tun.ko` was built from reconstructed configuration, packaged against the exact kernel dependency, loaded on the router and exercised with UDP traffic.

中文：第二个包保留官方 `libnetfilter-conntrack3` 的用户态库二进制，只去掉其对缺失 `kmod-nf-conntrack-netlink` 的强制依赖。当前 DNS 配置不使用连接标记查询；这个重打包不提供 conntrack-netlink 内核功能。若将来需要该功能，必须重新评估，不能据此继续删除任意依赖。

English: The second package preserves the official `libnetfilter-conntrack3` userspace binary while removing its hard dependency on the unavailable `kmod-nf-conntrack-netlink`. The tested DNS configuration does not use connection-mark queries. This does not supply the missing kernel API. Any future feature needing that API requires a separate compatibility assessment; this is not a general method for deleting dependencies.

## 8. 安装包与核心 / Install packages and the core

中文：先模拟安装并检查计划。正常计划会把精简 `dnsmasq` 换成 `dnsmasq-full`；保留原 DHCP 配置。若计划删除无线驱动、替换 kernel 或出现不满足的内核依赖，应停止。下列命令是本次成功使用的安装组合，不是官方对任意设备的通用依赖清单。官方通常列出的依赖见 [OpenClash 发布说明](https://github.com/vernesong/OpenClash/releases/tag/v0.48.002)。

English: Simulate the transaction first. Replacing minimal `dnsmasq` with `dnsmasq-full` is expected, while existing DHCP configuration must be retained. Stop if the plan replaces the kernel, removes wireless drivers or reports unmatched kernel dependencies. This is the transaction used in this case, not a universal dependency list. See the [official release instructions](https://github.com/vernesong/OpenClash/releases/tag/v0.48.002) for upstream requirements.

```sh
# Router / 路由器
apk update
apk --simulate add --allow-untrusted \
  /tmp/kmod-tun-6.12.93-r100.apk \
  /tmp/libnetfilter-conntrack3-1.1.0-r100.apk \
  /tmp/luci-app-openclash-0.48.002.apk ip-full

# Only after reviewing the simulation / 检查模拟结果后执行
apk --cache-predownload add --allow-untrusted \
  /tmp/kmod-tun-6.12.93-r100.apk \
  /tmp/libnetfilter-conntrack3-1.1.0-r100.apk \
  /tmp/luci-app-openclash-0.48.002.apk ip-full

mkdir -p /etc/openclash/core
gzip -dc /tmp/mihomo-linux-arm64-v1.19.32.gz > /etc/openclash/core/clash_meta
chmod 755 /etc/openclash/core/clash_meta
/etc/openclash/core/clash_meta -v
modprobe tun
test -c /dev/net/tun
ip tuntap add dev ocprobe0 mode tun
ip link show ocprobe0
ip tuntap del dev ocprobe0 mode tun
```

中文：`--allow-untrusted` 只用于已校验的本地适配包及官方应用 APK，不应变成全局关闭校验。不要增加 `--force-overwrite`、忽略依赖或 `insmod -f`。TUN 的开机加载文件已包含在适配 APK 内。

English: `--allow-untrusted` is scoped to the verified local packages and official application APK; it should not become a global bypass. Do not add forced overwrite, ignored dependencies or `insmod -f`. The adapted TUN APK includes its boot-load configuration.

中文：替换 DNS 软件包后，检查 `/etc/config/dhcp`、可能产生的 `.apk-new` 文件和 DHCP 地址池，再启动 DNS 与广告过滤。不要用默认 `.apk-new` 覆盖现有 DHCP 配置。

English: After replacing DNS packages, inspect `/etc/config/dhcp`, any `.apk-new` file and the DHCP pool. Do not overwrite the existing DHCP configuration with the newly supplied default.

```sh
/etc/init.d/dnsmasq restart
/etc/init.d/adblock-fast restart
```

## 9. 三个 Wi-Fi / Three wireless networks

中文：配置 `Cudy-2.4G`、`Cudy-5G` 与 `Cudy-MLO`，全部属于 `lan`。MLO 使用同一个多链路 AP，绑定两块无线设备，采用 WPA3-SAE 和必需的管理帧保护。详细操作及完整示例见 [Wi-Fi 章节](WIFI-MLO.md)。

English: Configure `Cudy-2.4G`, `Cudy-5G` and `Cudy-MLO`, all attached to `lan`. MLO uses one multi-link AP across both radios with WPA3-SAE and required management-frame protection. See the [wireless chapter](WIFI-MLO.md) for detailed instructions and examples.

## 10. 安装与配置防广告 / Install and configure ad blocking

中文：本次使用 AdBlock Fast `1.2.4-r4`，后端为 `dnsmasq.servers`，启用 Hagezi Pro 列表和压缩缓存。安装加速处理所需的工具，避免出现缺少 gawk/grep/sed/sort 的提示。服务菜单中文翻译包可按软件源提供情况选择。

English: The tested installation used AdBlock Fast `1.2.4-r4`, the `dnsmasq.servers` backend, Hagezi Pro and compressed caching. Install its processing tools to avoid missing-tool warnings. The Chinese LuCI translation package is optional and feed-dependent.

```sh
# Router / 路由器
apk add adblock-fast luci-app-adblock-fast gawk grep sed coreutils-sort
uci set adblock-fast.config.enabled='1'
uci set adblock-fast.config.force_dns='0'
uci set adblock-fast.config.compressed_cache='1'
uci commit adblock-fast
/etc/init.d/adblock-fast enable
/etc/init.d/adblock-fast restart
```

中文：在 LuCI 的服务 → AdBlock Fast 中确认 DNS 后端为 `dnsmasq.servers`，Hagezi Pro 已启用。本文不启用 AdBlock Fast 的强制 DNS 劫持，因为 OpenClash 负责对应的 DNS 接管。最终链路为客户端 → dnsmasq 广告过滤 → Mihomo DNS。将自己的订阅域名加入允许列表，填写域名即可，不要把完整订阅 token 当域名填进去。

English: In Services → AdBlock Fast, confirm the `dnsmasq.servers` backend and enable Hagezi Pro. AdBlock Fast's forced DNS redirection remains disabled because OpenClash manages DNS interception. The intended chain is client → dnsmasq filtering → Mihomo DNS. Allow-list your subscription hostnames if necessary, without inserting their full token-bearing URLs.

中文：列表生成可能需要一段时间。检查服务日志和实际查询，不要只看启动项。实机最终报告拦截 201729 个域名；列表会变化，这不是以后必须完全相同的数字。官方行为与设置说明见 [AdBlock Fast 文档](https://docs.mossdef.org/adblock-fast/)。

English: List generation can take time. Check logs and actual DNS responses, not only the enabled flag. The recorded list contained 201729 blocked domains; future list revisions need not match that count. See the [maintainer's documentation](https://docs.mossdef.org/adblock-fast/) for service behavior and settings.

## 11. 准备两份私人订阅 / Prepare two private subscriptions

中文：订阅应为 Mihomo/Clash YAML，包含非空 `proxies` 列表。本例两份订阅共有 107 条原始条目，其中可能含套餐信息节点；这不等同于 107 条独立、有效、可用的线路。本仓库不发布真实订阅或节点。

English: Each subscription must be a Mihomo/Clash YAML document with a nonempty `proxies` list. The two originals contained 107 raw entries, which can include informational entries; that does not establish 107 independent working endpoints. Real subscriptions and nodes are not published.

中文：在电脑创建 `private/urls.json`，内容是两个 HTTPS URL 的 JSON 数组，并把两份下载好的订阅保存为 `private/subscription-1.yaml`、`private/subscription-2.yaml`。可使用文本编辑器输入链接，避免写进命令历史。若服务返回 Base64 节点集合或 HTML 错误页，应先在服务商侧选择 Clash 格式，不能直接当 YAML 合并。

English: Create `private/urls.json` on the computer as a JSON array of two HTTPS URLs. Save the downloaded YAML documents as `private/subscription-1.yaml` and `private/subscription-2.yaml`. Use a text editor to keep URLs out of shell history. Base64 node lists and HTML errors must be converted or corrected at the provider before use.

```json
[
  "https://subscription-one.example.invalid/REPLACE_WITH_PRIVATE_TOKEN",
  "https://subscription-two.example.invalid/REPLACE_WITH_PRIVATE_TOKEN"
]
```

```sh
# Computer / 电脑
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
chmod 600 private/urls.json private/subscription-1.yaml private/subscription-2.yaml
.venv/bin/python scripts/make_config.py \
  --subscription-one private/subscription-1.yaml \
  --subscription-two private/subscription-2.yaml \
  --urls-file private/urls.json
```

中文：生成器保留第二份订阅的规则与分类策略组，把两份节点作为 HTTP proxy-providers，增加总选择、自动测速和两份订阅各自的选择组。它还生成随机控制器密钥，并设置私人输出权限为 `600`。生成器是本次脚本的公开泛化版本，必须用 Mihomo 检查你的实际订阅，不能假设适配所有服务商格式。

English: The generator retains the second subscription's rules and category groups, exposes both node sets as HTTP proxy providers, and adds a master selector, automatic selection and per-subscription selectors. It generates a random controller secret and writes private outputs with mode `600`. This public helper generalizes the original script; validate your actual inputs with Mihomo rather than assuming every provider format is supported.

```sh
# Router / 路由器
mkdir -p /etc/openclash/config /etc/openclash/proxy_provider
```

```sh
# Computer / 电脑
scp -O private/generated/Cudy-OpenClash.yaml root@192.168.10.1:/etc/openclash/config/
scp -O private/generated/provider-1.yaml root@192.168.10.1:/etc/openclash/proxy_provider/subscription-1.yaml
scp -O private/generated/provider-2.yaml root@192.168.10.1:/etc/openclash/proxy_provider/subscription-2.yaml
scp -O scripts/configure_openclash.sh scripts/rollback_guard.sh root@192.168.10.1:/tmp/
```

## 12. 校验配置并保持关闭 / Validate before enabling

```sh
# Router / 路由器
chmod 600 /etc/openclash/config/Cudy-OpenClash.yaml /etc/openclash/proxy_provider/subscription-*.yaml
SAFE_PATHS=/usr/share/openclash:/etc/ssl \
  /etc/openclash/core/clash_meta -t -d /etc/openclash \
  -f /etc/openclash/config/Cudy-OpenClash.yaml
sh /tmp/configure_openclash.sh
```

中文：必须看到配置测试成功。`SAFE_PATHS` 与 OpenClash 的启动环境相配套，避免手动测试因为外部 UI 路径而误报安全路径错误。如果模板引用了尚未安装的面板目录，在 LuCI 版本更新中安装所选面板，或先取消该 UI 路径再测；不要用关闭路径保护来绕过。

English: Require a successful configuration test. `SAFE_PATHS` matches OpenClash's startup environment and avoids a misleading manual-test failure for the external UI path. If the selected dashboard is missing, install it through LuCI or omit that UI path before testing; do not disable path protection.

中文：配置脚本采用最终验证的 `fake-ip-mix`，并启用中国 IP 绕过。它保持插件关闭，留出检查和回退准备时间。与早期尝试的全 TUN 设置相比，公开脚本以最终实机设置为准。IPv6 代理和进程识别关闭；LAN 的原有 IPv6 RA/DHCPv6 不会因此自动关闭。

English: The helper selects the final tested `fake-ip-mix` configuration with China-IP bypass. It leaves OpenClash disabled until recovery preparation is complete. These final settings supersede an earlier all-TUN trial. IPv6 proxying and process recognition remain off; existing LAN IPv6 RA/DHCPv6 is a separate setting.

## 13. 定时任务、回退计时与启动 / Cron, rollback timer and activation

中文：精简系统可能还没有 root 的计划任务文件。本次启动时因此出现提示，创建空文件并开启 cron 后解决。不要覆盖已有任务。

English: Minimal systems may have no root crontab. Creating the missing file and enabling cron resolved that startup warning in this case. Preserve any existing entries.

```sh
# Router / 路由器
mkdir -p /etc/crontabs
test -e /etc/crontabs/root || touch /etc/crontabs/root
chmod 600 /etc/crontabs/root
/etc/init.d/cron enable
/etc/init.d/cron start

# Arm a 15-minute rollback, then enable / 先启动 15 分钟回退计时，再启用
nohup sh /tmp/rollback_guard.sh arm /tmp/oc-before 900 \
  > /tmp/oc-rollback.log 2>&1 < /dev/null &
echo $! > /tmp/oc-before/guard.pid
uci set openclash.config.enable='1'
uci commit openclash
/etc/init.d/openclash enable
/etc/init.d/openclash start
```

中文：在计时到期前完成下一节验证，再确认保留配置。若计时已经触发回退，不能仅创建确认文件就宣称成功：应重新检查、使用新的快照目录和计时器，再启用插件。这个回退只停止代理并恢复 DHCP、防火墙配置，不卸载新软件包，也不恢复完整固件。重启会使 `/tmp` 中的计时器失效，测试期间不要依赖它跨重启恢复。

English: Complete the next section and confirm before the deadline. If rollback already fired, creating a confirmation file is insufficient; inspect the result, create a fresh snapshot directory and re-arm before enabling again. The guard stops OpenClash and restores DHCP/firewall configuration; it does not uninstall packages or restore firmware. It lives in `/tmp` and is not a reboot-persistent recovery mechanism.

## 14. 验证与确认 / Verify and confirm

**路由器 / Router:**

```sh
test -c /dev/net/tun
pgrep -f clash_meta
uci get openclash.config.en_mode
ip -4 rule
ip -4 route
nslookup www.baidu.com 127.0.0.1
/etc/init.d/adblock-fast status
```

中文：LuCI 的服务 → OpenClash 应显示 Meta 核心运行。首次安装后若菜单没出现，退出 LuCI 再用原口令登录，以更新会话权限缓存。每个订阅分别选择真实节点测试，不要把“剩余流量”之类信息条目误选为出口。总策略组选择“自动选择”，分类组选择“代理”或合适的出口；如果分类组仍选着失效条目，部分应用会失败。

English: Services → OpenClash should show the Meta core running. If the menu is missing after installation, log out and back into LuCI to refresh session ACLs. Test a real endpoint from each subscription; informational quota entries are not useful exits. Set the master group to automatic selection and category groups to the intended proxy. A stale category selection can break only some applications.

**电脑 / Computer, macOS — change interface names if necessary:**

```sh
networksetup -getinfo Wi-Fi
dig @192.168.10.1 www.baidu.com A
dig @192.168.10.1 pagead2.googlesyndication.com A
curl --noproxy '*' --interface en1 -4 --connect-timeout 5 --max-time 15 \
  -o /dev/null -sS -w '%{http_code}\n' http://www.baidu.com/
```

中文：正常域名应解析；本次广告域名返回 NXDOMAIN。广告过滤有范围限制：与正常内容共用域名的广告、客户端绕过路由器 DNS 的流量，不一定被这种 DNS 过滤拦截。

English: Normal domains should resolve; the tested advertising domain returned NXDOMAIN. DNS-based filtering has limits: advertisements sharing content domains and clients bypassing router DNS may not be blocked.

中文：如果电脑另有 VPN/代理，普通浏览器测试可能走电脑自己的代理。应指定物理网卡，并从路由器 DNS 取得测试域名的当前地址；如本机 VPN 使用另一套 Fake-IP，直接使用它的解析结果可能造成误判。下面的 IP 必须替换为刚查询到的值，不能永久保存某个公网 IP。

English: A separate computer VPN can make an ordinary browser test bypass the router proxy. Bind the physical interface and use a current address returned by the router's DNS. A local VPN's unrelated Fake-IP mapping can otherwise mislead the test. Replace the example with the freshly queried address; do not permanently pin a public IP.

```sh
# Computer / 电脑
dig @192.168.10.1 www.gstatic.com A +short
curl --noproxy '*' --interface en1 -4 \
  --resolve www.gstatic.com:443:REPLACE_WITH_CURRENT_DNS_ANSWER \
  --connect-timeout 5 --max-time 15 -o /dev/null -sS \
  -w 'HTTP=%{http_code} source=%{local_ip}\n' \
  https://www.gstatic.com/generate_204
```

中文：HTTP 204 是该测试地址的预期响应。还应验证 UDP：本次对 Cloudflare 和 Google 的 STUN 服务发出标准请求，均收到合法响应，并通过 Mihomo 连接记录核实代理链。TUN 设备存在只说明驱动加载，不能替代真实 UDP 数据流验证。

English: HTTP 204 is expected for this endpoint. UDP must also be checked: valid STUN responses from Cloudflare and Google were received in this case, with the proxy chain confirmed in Mihomo connection metadata. The existence of a TUN device alone does not prove UDP traffic is working.

**验证通过后，路由器 / After passing checks, on router:**

```sh
sh /tmp/rollback_guard.sh confirm /tmp/oc-before
sha256sum -c /tmp/oc-before/network-wireless.sha256
```

中文：上面的哈希检查用于只安装 OpenClash 的阶段；如果你在同一阶段主动改过 Wi-Fi 或 LAN，变化应逐项核对，不能要求哈希仍相同。本次安装插件前后网络和无线配置未变，后来排查交换机时单独删除了重复 LAN 地址。

English: The hash check applies to the OpenClash-only installation phase. If you intentionally changed LAN or wireless configuration during that phase, review those differences rather than expecting identical hashes. In this case installation preserved both files; the later switch investigation separately removed the duplicate LAN address.

## 15. 交换机接入与有线验证 / Connect and verify the switch

中文：保持光猫到 WAN 的连接，再把 LAN 接交换机，将电脑接到交换机。查看 `eth1` 的 carrier、速率和 DHCP 租约。`carrier=0` 说明此刻没有物理链路，不能据此判定软件桥接有问题；`carrier=1`、`speed=1000` 表示建立千兆链路。

English: Keep modem → WAN, connect LAN → switch, then connect a computer to the switch. Check `eth1` carrier, speed and DHCP leases. `carrier=0` means no physical link at that moment; it does not establish a bridge configuration fault. `carrier=1` and `speed=1000` indicate a gigabit link.

```sh
# Router / 路由器
cat /sys/class/net/eth1/carrier
cat /sys/class/net/eth1/speed
cat /sys/class/net/eth1/duplex
brctl show
cat /tmp/dhcp.leases
```

```sh
# Computer / 电脑
networksetup -getinfo Ethernet
ipconfig getpacket en0
curl --noproxy '*' --interface en0 -4 --connect-timeout 5 --max-time 15 \
  -o /dev/null -sS -w 'HTTP=%{http_code} source=%{local_ip}\n' http://192.168.10.1/
python3 scripts/verify_wired_dns.py --interface en0 --address YOUR_CURRENT_WIRED_IP
```

中文：本次 Mac 从交换机这条有线路径获得 `192.168.10.111`，网关与 DNS 都是 `192.168.10.1`。绑定 `en0` 后，后台、普通 HTTP/HTTPS 和代理 HTTPS 测试均成功。其他电脑若仍是固定 `192.168.1.x`，应改用 DHCP，或规划正确的 `192.168.10.x` 静态地址。详细故障分支见 [排障章节](TROUBLESHOOTING.md)。

English: The tested Mac obtained `192.168.10.111` over the reported switch path, with gateway and DNS `192.168.10.1`. Explicit Ethernet tests passed for LuCI, ordinary HTTP/HTTPS and proxied HTTPS. Other computers with fixed `192.168.1.x` settings should use DHCP or correctly planned LAN static addresses. See [troubleshooting](TROUBLESHOOTING.md) for the decision tree.

## 16. 手动回退 / Manual rollback

中文：若启动代理后出现问题，优先停用插件并恢复原 DNS、防火墙配置，保留后台连接。以下命令不会恢复出厂或刷写固件。若已经重启，先从电脑备份把快照目录复制回路由器。

English: If activation causes trouble, stop the proxy and restore DNS/firewall configuration while retaining management access. These commands do not factory-reset or flash the router. After a reboot, copy the snapshot back from the private computer backup first.

```sh
# Router / 路由器
sh /tmp/rollback_guard.sh restore /tmp/oc-before
```

中文：不要在服务运行时强行卸载 TUN，不要直接删除 dnsmasq-full。恢复普通上网后，再根据 APK 依赖关系规划卸载。完整配置恢复可使用 LuCI 的备份恢复功能，但包含原来的网络设置，会影响当前地址，执行前应核对文件内容。本次没有需要进行这一步。

English: Do not force-remove a loaded TUN module or delete dnsmasq-full first. Restore ordinary connectivity, then plan package removal using the dependency graph. Full configuration restoration through LuCI also restores old networking and can change the management address; inspect the backup first. It was not needed here.

## 17. 后续更新的边界 / Future updates

中文：升级系统固件或 kernel 包后，应重新检查自编 TUN 模块。不要为了安装新内核模块而对这台快照执行全量 `apk upgrade`。更新 OpenClash/Mihomo 时先备份配置，阅读版本变化，验证新的核心与当前内核功能是否仍兼容。

English: Reassess the custom TUN module after any firmware or kernel-package change. Do not run a blanket `apk upgrade` on this snapshot to obtain an unrelated kernel module. Before application/core updates, back up configuration, review release changes and test compatibility with the retained kernel facilities.

中文：当前未启用 IPv6 透明代理。IPv6 字面地址或未被当前规则接管的流量可能直连；不能宣称所有协议、所有应用都必经代理。MLO 也不保证任意客户端把两频段速率简单相加。本文记录已验证的功能和限制，不把“运行中”标志当作所有能力的证明。

English: IPv6 transparent proxying remains disabled. Literal IPv6 destinations and traffic outside interception may go direct; not every protocol or application is guaranteed to traverse the proxy. MLO likewise does not guarantee additive link speeds for every client. The guide distinguishes verified behavior from unsupported assumptions.
