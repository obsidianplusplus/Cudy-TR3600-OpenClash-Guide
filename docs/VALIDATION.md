# 实机验证与公开脚本检查 / Device validation and helper checks

[返回首页 / Back](../README.md)

## 1. 实机安装结果 / Original device results — 2026-10-18

| 项目 / Check | 结果 / Result | 实际范围 / Scope |
|---|---|---|
| TUN module load | PASS | No forced load; `/dev/net/tun` created |
| TUN interface create/delete | PASS | `ip tuntap` probe |
| OpenClash application | PASS | Official LuCI 0.48.002 |
| Mihomo core | PASS | ARM64 1.19.32, gVisor |
| Boot startup configuration | PASS | OpenClash + adblock enabled; TUN autoload packaged |
| Subscription 1 HTTPS | HTTP 204 | Explicit proxy test with that provider |
| Subscription 2 HTTPS | HTTP 204 | Explicit proxy test with that provider |
| Wi-Fi direct website | HTTP 200 | Mac physical Wi-Fi interface |
| Wi-Fi proxy website | HTTP 204 | Current router DNS address + interface-bound HTTPS |
| Wi-Fi UDP STUN | PASS | Valid Cloudflare and Google responses; proxy-chain metadata checked |
| Three SSIDs | PASS | Each joined and HTTP tested |
| MLO AP configuration | PASS | AP exposes two radio links |
| MLO aggregate speed benchmark | Not performed / 未执行 | No throughput claim |
| IPv6 transparent proxy | Not enabled / 未启用 | Existing LAN IPv6 service retained |
| nft TPROXY module | Not installed / 未安装 | Candidate lacked required original-kernel exports |
| Process recognition | Disabled / 关闭 | Not part of the tested mode |
| AdBlock Fast | PASS | 201729 domains; test advertising domain NXDOMAIN |

中文：开启启动项不等于已经验证过所有可能的重启场景。页面截图显示运行状态，不能单独证明端到端网络能力；表中的网络测试才是对应功能证据。没有进行长时间稳定性、最大吞吐或所有节点逐一可用性测试。

English: Enabling startup entries is not a claim that every reboot scenario was tested. The screenshot establishes application state, while the traffic checks establish the listed network functions. Long-duration stability, maximum throughput and every individual endpoint were not exhaustively tested.

## 2. 有线接入复核 / Wired follow-up — 2026-10-18

中文：用户接好 LAN → 交换机 → Mac 后，实测如下。物理拓扑由用户报告，交换机作为透明设备不提供单独的路由跳数。下游其他电脑未逐台测试。

English: After the user reported connecting LAN → switch → Mac, the following measurements were taken. A transparent switch does not appear as a routed hop. Other downstream computers were not tested individually.

| 项目 / Check | 结果 / Result |
|---|---|
| Router LAN interface | `eth1`, carrier 1, 1000 Mbit/s, full duplex |
| Mac wired interface | `en0`, DHCP `192.168.10.111/24` |
| DHCP server, gateway, DNS | `192.168.10.1` |
| Wired LuCI request | HTTP 200, source `.10.111` |
| Wired ordinary HTTP | HTTP 200, source `.10.111` |
| Wired ordinary HTTPS | HTTP 200, source `.10.111`, TLS verification retained |
| Wired proxied HTTPS | HTTP 204, source `.10.111` |
| Wired UDP DNS normal name | RCODE 0, answers received |
| Wired UDP DNS advertising name | RCODE 3 / NXDOMAIN |
| Wired STUN application test | Not separately performed / 未单独执行 |

中文：所有有线 TCP 测试显式绑定 `en0`，DNS 测试使用 Darwin `IP_BOUND_IF`，避免同时连接的 Wi-Fi 或电脑 VPN 影响路径判断。普通 HTTPS 与代理 HTTPS 测试使用从路由器取得的当前 DNS 结果，避免电脑另一套 Fake-IP 映射的干扰。

English: Wired TCP requests explicitly used `en0`; DNS used Darwin `IP_BOUND_IF`, avoiding ambiguity from concurrent Wi-Fi or computer VPN interfaces. HTTPS tests used current router-DNS answers to avoid the computer VPN's separate Fake-IP mapping.

## 3. 文档辅助脚本 / Documentation helpers — 2026-10-19

中文：公开脚本是为教程整理的版本，不是直接上传私人脚本。检查包括 shell/Python 语法、配置合并后的策略引用、随机密钥与文件权限、输入格式拒绝、下载哈希失败处理，以及文档本地链接与文件清单。它们没有在当前路由器上重新执行一遍安装，避免无必要地中断已运行网络。

English: Public helpers were prepared for this guide rather than copied with private settings. Checks cover shell/Python syntax, merged proxy references, random secrets and file permissions, invalid-input rejection, download checksum failures, local documentation links and asset inventories. The live router was not reinstalled merely to validate documentation.

中文：原始实机 APK、核心和编译配置的哈希已经归档。重建产物如果不同，应重新核对环境与实际兼容性；不应修改校验清单来冒充原产物。

English: Original package, core and configuration digests are archived. A differing rebuild must be assessed on its own environment and compatibility; changing the manifest does not make it the original artifact.
