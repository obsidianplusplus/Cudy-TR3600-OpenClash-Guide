# 交换机与常见故障排查 / Switch and general troubleshooting

[返回首页 / Back](../README.md)

## 1. 本次有线故障的证据 / Evidence from this wired-network incident

中文：用户报告手机连接 Cudy Wi-Fi 可以上网，交换机下的有线电脑不通。先前仅凭现象只能列出候选原因；远程检查后发现了确实存在的 LAN 配置冲突：

English: The reported symptom was working phone Wi-Fi but failed wired clients behind a switch. Initial hypotheses were not a diagnosis. Remote inspection then established a concrete LAN configuration error:

```text
LAN before:
  192.168.10.1/24
  192.168.1.1/24       <- also the modem's address
WAN:
  192.168.1.5/24
  default via 192.168.1.1 dev eth0

route lookup before:
  local 192.168.1.1 dev lo table local

LAN after:
  192.168.10.1/24
route lookup after:
  192.168.1.1 dev eth0 src 192.168.1.5
```

中文：修复只删除重复的 LAN 地址，保留管理地址。第一次检查时 LAN 线尚未接通；用户随后接好，LAN 建立千兆全双工连接，Mac 有线网卡收到 DHCP 地址 `192.168.10.111`，绑定有线接口测试后台、HTTP、HTTPS 和代理 HTTPS 均成功。因此可确认配置冲突已修复、被测有线路径现已正常，但不能把所有以前的失败都仅凭这一项追溯为同一原因。

English: The change removed only the duplicated LAN address. At first the LAN cable was disconnected. After the user connected it, the link negotiated 1 Gbit/s full duplex, the Mac received `192.168.10.111`, and Ethernet-bound management, HTTP, HTTPS and proxied HTTPS tests passed. This establishes a corrected overlap and a working tested path; it does not prove every prior failure had that single cause.

```sh
# Router / 路由器; applies only when this exact duplicate exists
cp -p /etc/config/network /tmp/network-before-overlap-fix.conf
uci del_list network.lan.ipaddr='192.168.1.1/24'
uci commit network
ubus call network reload
```

## 2. 先分清故障范围 / Establish the failure scope

| 现象 / Symptom | 优先检查 / First checks |
|---|---|
| Wi-Fi 正常，所有有线电脑不通 / Wi-Fi works, all wired fail | LAN uplink, switch, VLAN, DHCP delivery |
| 只有一台电脑不通 / One computer fails | Client static IP, gateway, DNS, cable, local VPN |
| 有线和 Wi-Fi 一起失败 / Both wired and Wi-Fi fail | WAN lease, gateway, DNS, proxy status, loops |
| 能开后台但域名打不开 / LuCI works, names fail | DNS settings, dnsmasq, Mihomo DNS, block-list reload |
| 国内可用，部分应用失败 / Some apps or destinations fail | Category group selection, node health, UDP, IPv6 behavior |

中文：Wi-Fi 能用可以缩小范围，但不能单凭它证明所有有线策略或每个客户端都正常。下列步骤从物理连接逐步推进，避免先改全局代理设置。

English: Working Wi-Fi narrows the investigation but does not prove all wired policies or clients are healthy. Follow physical-to-IP-to-DNS-to-proxy checks rather than changing global proxy settings first.

## 3. 物理链路 / Physical link

```sh
# Router / 路由器
cat /sys/class/net/eth1/carrier
cat /sys/class/net/eth1/speed
cat /sys/class/net/eth1/duplex
ip -s link show eth1
```

中文：`carrier=0` 时依次检查电源、网线、端口。可用已知正常的网线和电脑暂时直连 LAN，对比直连与经过交换机的结果；这一步需要现场操作。千兆交换机接 2.5G 路由口通常会协商共同支持的速率，速率不同本身不是“完全无法上网”的证据。

English: With `carrier=0`, check switch power, cable and ports. A known-good computer and cable connected directly to LAN can isolate the switch path; this requires local physical access. A gigabit switch normally negotiates a shared supported speed with a 2.5G router port; unequal headline speeds alone do not explain total loss of Internet.

中文：若是管理型交换机，检查上联和客户端端口是否属于同一正确 VLAN，是否启用隔离。避免两条线路绕回同一个二层网络形成环路。双 DHCP 和二层环路是不同问题：额外接一台路由器可能带来错误地址分配，环路则需要实际存在循环的二层连接。

English: On a managed switch, check VLAN membership and isolation for uplink and client ports. Avoid redundant cabling that forms an actual layer-2 loop. Multiple DHCP servers and bridging loops are different faults: another router can supply unwanted leases, while a loop requires a cyclic layer-2 path.

## 4. DHCP 与客户端地址 / DHCP and client configuration

```sh
# Router / 路由器
uci show dhcp.lan
cat /tmp/dhcp.leases
logread | sed -n '/DHCPDISCOVER/p; /DHCPOFFER/p; /DHCPACK/p; /DHCPNAK/p' | tail -n 50
```

| 客户端地址 / Client address | 含义 / Interpretation |
|---|---|
| `192.168.10.x`, gateway `.10.1` | Expected LAN addressing / 符合规划 |
| `169.254.x.x` | No usable DHCP lease / 没有取得有效 DHCP 地址 |
| `192.168.1.x` | Old static settings, stale lease or another DHCP source / 旧配置、旧租约或其他 DHCP |
| `.10.x` but wrong gateway/DNS | Inspect manual overrides / 检查手动覆盖项 |

中文：Windows 可运行 `ipconfig /all` 查看以太网配置；设为自动获取后，可用 `ipconfig /release`、`ipconfig /renew` 重新申请。macOS 在系统设置的以太网 TCP/IP 中选择 DHCP、续租。不要为了修复一台电脑，把整个 LAN 改回与光猫重叠的网段。

English: On Windows, inspect Ethernet with `ipconfig /all`; after selecting automatic addressing, renew using `ipconfig /release` and `ipconfig /renew`. On macOS choose DHCP and renew in Ethernet TCP/IP settings. Do not move the entire LAN into the modem's subnet to accommodate one stale client.

## 5. 桥接、路由与防火墙 / Bridge, routing and firewall

```sh
# Router / 路由器
ubus call network.device status '{"name":"br-lan"}'
brctl show
brctl showmacs br-lan
ip -4 addr
ip -4 route
ip -4 route get 192.168.1.1
nft list chain inet fw4 forward_lan
nft list chain inet fw4 srcnat_wan
```

中文：本次 `br-lan` 成员应包括 `eth1` 和各 AP；不应把 WAN `eth0` 放进 LAN 桥。防火墙应允许 LAN 到 WAN 的转发，WAN 开启 IPv4 masquerade。交换机为透明设备，不一定会作为有 IP 的客户端显示在租约表里；应查看它后面电脑的 MAC 学习与地址。

English: The tested bridge includes `eth1` and the AP interfaces, not WAN `eth0`. Firewall forwarding should allow LAN → WAN and enable WAN IPv4 masquerading. A transparent switch may have no DHCP lease of its own; look for downstream clients and learned MACs instead.

## 6. DNS、防广告与代理 / DNS, filtering and proxy

```sh
# Computer / 电脑
dig @192.168.10.1 www.baidu.com A
dig @192.168.10.1 pagead2.googlesyndication.com A
```

中文：正常域名应有有效响应；本次广告域名预期 NXDOMAIN。若列表正在下载或 DNS 服务尚在重载，待日志完成后复测。AdBlock Fast 的运行方式是生成 DNS 列表后退出，因此没有常驻进程并不等于停止过滤。检查 `servers-file` 配置和真实查询。

English: Normal domains should resolve and the test advertisement should return NXDOMAIN in this configuration. Retest after list generation and DNS reload finish. AdBlock Fast generates resolver files and exits; absence of a permanent process does not mean filtering is off. Inspect `servers-file` and real DNS results.

```sh
# Router / 路由器
uci -q get dhcp.@dnsmasq[0].serversfile
sed -n '/servers-file/p; /server=/p' /var/etc/dnsmasq.conf.*
pgrep -f clash_meta
uci get openclash.config.en_mode
```

中文：直接连接 OpenClash HTTP 代理端口返回 `407`，可能只是缺少代理认证，不是透明代理故障。不要因此移除认证。LuCI/控制器管理口和手动代理口应继续限制在可信内网；当前 WAN 防火墙拒绝外部访问。

English: HTTP `407` from a manually addressed proxy port can simply mean missing proxy authentication, not broken transparent routing. Do not remove authentication to silence it. Keep management/controller and explicit proxy ports limited to the trusted LAN; the tested WAN firewall rejects inbound access.

中文：如果只有某类应用失败，检查分类策略组是否仍选中失效或信息节点。确认 TCP 与 UDP 分别可用。IPv6 代理关闭时不能把 IPv6 直连现象当成 IPv4 TUN 失效的证据。

English: For application-specific failure, inspect category groups for stale or informational selections. Verify TCP and UDP separately. With IPv6 proxying disabled, direct IPv6 traffic does not by itself establish a failed IPv4 TUN.

## 7. 电脑同时有线、Wi-Fi 与 VPN / Multiple computer interfaces and a VPN

中文：最初 Mac 的网线接光猫，Wi-Fi 接 OpenWrt，分别属于 `.1.x` 和 `.10.x`，这本身可以共存。后来网线经交换机接到 OpenWrt，地址变成 `.10.111`。如果电脑上同时有代理/VPN，默认路由与 DNS 可能由它接管，普通测速不能证明经过路由器代理。

English: Initially the Mac used modem Ethernet (`.1.x`) and OpenWrt Wi-Fi (`.10.x`), which can coexist. After connection through the switch, Ethernet changed to `.10.111`. A computer VPN can control default routes and DNS, so an ordinary speed test does not establish router-proxy usage.

中文：使用 `networksetup -listallhardwareports` 确认网卡，使用 `curl --interface en0` 指定有线接口，并确认输出的 `local_ip` 是当前有线地址。DNS 则使用附带的 macOS 验证脚本绑定物理接口。测试 HTTP/HTTPS 时如需指定解析结果，只用刚从路由器取得的地址，不关闭 TLS 证书验证。

English: Identify adapters with `networksetup -listallhardwareports`, bind `curl --interface en0` and verify its `local_ip`. The included macOS DNS helper explicitly binds the physical interface. Where necessary, use a freshly queried router-DNS address for HTTP/HTTPS tests, retaining TLS certificate validation.
