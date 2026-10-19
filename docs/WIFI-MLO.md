# 三个 Wi-Fi 与 MLO / Three Wi-Fi networks and MLO

[返回首页 / Back](../README.md)

## 1. 最终设置 / Final settings

| 名称 / SSID | 无线设备 / Radio | 加密 / Encryption | PMF |
|---|---|---|---|
| `Cudy-2.4G` | `radio0` | WPA2/WPA3 personal, `sae-mixed` | Optional / 可选 (`1`) |
| `Cudy-5G` | `radio1` | WPA2/WPA3 personal, `sae-mixed` | Optional / 可选 (`1`) |
| `Cudy-MLO` | `radio0` + `radio1`, one MLO AP | WPA3-SAE, `sae` | Required / 必需 (`2`) |

中文：三个网络都桥接到 `lan`，共用 OpenWrt 的 DHCP、DNS、防广告和代理规则。实际部署可共用一个私人 Wi-Fi 密码，但不应使用后台管理口令作为公开示例。本文只提供占位符。

English: All three networks join `lan`, sharing DHCP, DNS, filtering and routing policies. They can use one private Wi-Fi password; this guide publishes placeholders rather than deployment credentials.

## 2. 操作前确认 / Before making changes

中文：先备份 `/etc/config/wireless`，最好通过已验证的有线 LAN 管理。无线重载会让当前 Wi-Fi 连接短暂断开。确认此固件的 netifd、hostapd 和驱动支持 MLO；不能只因为硬件包装写了 Wi-Fi 7 就认定任何固件都能创建 MLO AP。

English: Back up `/etc/config/wireless` and preferably manage the router through a tested wired LAN connection. Reloading Wi-Fi interrupts wireless management briefly. MLO requires support in the firmware's netifd, hostapd and driver, not merely Wi-Fi 7 hardware branding.

```sh
# Router / 路由器
cp -p /etc/config/wireless /tmp/wireless-before-three-ssids.conf
ubus call network.wireless status
iw dev
```

中文：本次固件已有 `radio0` 与 `radio1`，由 mt7996e 驱动支持。记录的运行设置为 2.4 GHz 信道 1、EHT20，以及 5 GHz 信道 36、EHT80。信道与带宽是同一 radio 上各 SSID 共享的设置，不是给每个 SSID 单独创建一块物理无线网卡。监管域应依据设备使用地区与固件支持设置，本文没有进行跨区功率修改。

English: The tested firmware exposes `radio0` and `radio1` with the mt7996e driver. Observed settings were channel 1/EHT20 on 2.4 GHz and channel 36/EHT80 on 5 GHz. SSIDs sharing a radio also share its channel and width; adding an SSID does not add a physical radio. Use the appropriate supported regulatory settings for the deployment. No cross-region power modification was performed.

## 3. LuCI 操作 / LuCI procedure

中文：进入“网络 → 无线”。在 2.4 GHz radio 下添加接入点，名称 `Cudy-2.4G`，网络选 `lan`，加密选 WPA2/WPA3 混合，填写自己的密码。在 5 GHz radio 下同样添加 `Cudy-5G`。确认原默认 SSID 不再需要后可以禁用，保留其配置用于回退。

English: Open Network → Wireless. Add an AP on the 2.4 GHz radio named `Cudy-2.4G`, attach it to `lan`, choose WPA2/WPA3 mixed personal and enter your password. Repeat on 5 GHz as `Cudy-5G`. Disable unneeded original SSIDs after verification, retaining their definitions for rollback.

中文：对 MLO，创建一个多链路 AP，SSID 为 `Cudy-MLO`，同时选择两块 radio，启用 MLO，网络为 `lan`，加密选择 WPA3-SAE，PMF 设为必需。当前定制 LuCI 如果没有暴露多设备选项，可在确认驱动支持后，参考下一节 UCI 配置。

English: Create one multi-link AP named `Cudy-MLO`, select both radios, enable MLO, attach it to `lan`, use WPA3-SAE and require PMF. If the vendor LuCI does not expose multi-radio selection, use the following UCI example only after confirming firmware support.

## 4. UCI 配置示例 / UCI configuration example

中文：下面是应追加或编辑的 `wifi-iface` 段落，不是用于覆盖整个 `/etc/config/wireless` 的完整文件。保留现有 `wifi-device`、MAC、校准和驱动设置。`<YOUR_WIFI_PASSWORD>` 必须改为自己的密码。

English: These are `wifi-iface` sections to add or edit, not a complete replacement for `/etc/config/wireless`. Preserve existing `wifi-device`, MAC, calibration and driver settings. Replace `<YOUR_WIFI_PASSWORD>` before use.

```uci
config wifi-iface 'cudy_24g'
        option device 'radio0'
        option mode 'ap'
        option network 'lan'
        option ssid 'Cudy-2.4G'
        option encryption 'sae-mixed'
        option ieee80211w '1'
        option key '<YOUR_WIFI_PASSWORD>'
        option disabled '0'

config wifi-iface 'cudy_5g'
        option device 'radio1'
        option mode 'ap'
        option network 'lan'
        option ssid 'Cudy-5G'
        option encryption 'sae-mixed'
        option ieee80211w '1'
        option key '<YOUR_WIFI_PASSWORD>'
        option disabled '0'

config wifi-iface 'cudy_mlo'
        list device 'radio0'
        list device 'radio1'
        option mode 'ap'
        option network 'lan'
        option ssid 'Cudy-MLO'
        option encryption 'sae'
        option ieee80211w '2'
        option sae_pwe '2'
        option mlo '1'
        option key '<YOUR_WIFI_PASSWORD>'
        option disabled '0'
```

```sh
# Router / 路由器, after editing and checking the file
uci commit wireless
wifi reload
```

中文：同名但分别运行的两个普通 AP，不等同于真正的 MLO。这里的关键是同一个 `wifi-iface` 使用两条 `list device` 与 `mlo=1`；实际接口应由驱动创建为多链路 AP。

English: Two independent ordinary APs with the same SSID are not equivalent to MLO. The significant configuration is one `wifi-iface` with both `list device` entries and `mlo=1`, resulting in a driver-created multi-link AP.

## 5. 验证 / Verification

```sh
# Router / 路由器
iw dev
ubus call network.wireless status
brctl show
```

中文：本次可看到独立 AP `phy0.0-ap0`、`phy0.1-ap0`，以及带两个 link 的 `ap-mld0`。它们都在 `br-lan`。接口名称由驱动产生，不应写死为其他固件通用名称。用客户端分别连接三个 SSID，确认拿到 `192.168.10.x`、打开后台并访问外网。

English: This device exposed ordinary APs `phy0.0-ap0`/`phy0.1-ap0` and `ap-mld0` with two links, all attached to `br-lan`. Names are driver-generated and may differ on other firmware. Connect a client to each SSID, verify its LAN address, management access and Internet connectivity.

中文：三个 SSID 在本次都完成了连接及 HTTP 200 测试。MLO 的 AP 两链路配置已核实；没有进行客户端聚合吞吐量的基准测试。终端必须支持兼容的 MLO 才能利用多链路，普通 Wi-Fi 客户端看到 SSID或成功连接，并不证明两条链路同时传输。MLO 也不等于两频段标称速率简单相加。

English: All three SSIDs passed connection and HTTP 200 checks. The two-link AP configuration was verified, but no client aggregate-throughput benchmark was performed. Compatible client MLO support is necessary; merely seeing or joining the SSID does not prove simultaneous traffic on both links. Advertised band speeds are not simply additive.

## 6. 回退 / Rollback

```sh
# Router / 路由器, only when the saved file is the intended original
cp -p /tmp/wireless-before-three-ssids.conf /etc/config/wireless
wifi reload
```

中文：若已经重启，先从私人备份恢复该文件到 `/tmp`，不要误用其他设备的无线配置或校准数据。

English: After a reboot, retrieve the intended file from private backup first. Do not substitute another device's wireless or calibration data.
