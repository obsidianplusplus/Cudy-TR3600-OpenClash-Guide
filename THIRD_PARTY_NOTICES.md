# 上游来源与许可 / Upstream sources and notices

中文：原创教程与原创辅助脚本使用根目录 MIT 许可。以下第三方组件、配置输入、补丁和二进制保留上游许可；本仓库的 MIT 许可不重新授权它们。发布页提供两个适配包及其源码资料，官方 OpenClash/Mihomo 由下载脚本直接从上游获取。

English: Original prose and helper scripts use the root MIT license. Third-party components, configuration inputs, patches and binaries retain their upstream licenses and are not relicensed by that MIT file. Adapted packages and source materials are provided in the release; official OpenClash/Mihomo binaries are fetched directly upstream.

| 组件 / Component | 来源 / Source | 许可范围 / License context |
|---|---|---|
| Linux 6.12.93, TUN | https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.12.93.tar.xz | Kernel COPYING and file notices, GPL-2.0-only context |
| OpenWrt snapshot, kernel patches/configs | https://github.com/openwrt/openwrt/tree/c484731c5a | OpenWrt LICENSE and individual file notices |
| libnetfilter_conntrack 1.1.0 | https://www.netfilter.org/projects/libnetfilter_conntrack/ | GPL-2.0-or-later; upstream COPYING included in source |
| OpenClash 0.48.002 | https://github.com/vernesong/OpenClash/releases/tag/v0.48.002 | Upstream repository license and notices |
| Mihomo 1.19.32 | https://github.com/MetaCubeX/mihomo/releases/tag/v1.19.32 | Upstream repository license and dependency notices |
| AdBlock Fast | https://github.com/stangri/adblock-fast | Upstream license; installed from configured feeds |
| Hagezi lists | https://github.com/hagezi/dns-blocklists | Upstream list license; downloaded by AdBlock Fast |
| Lima 2.2.1 | https://github.com/lima-vm/lima/releases/tag/v2.2.1 | Build tool only, upstream license |
| PyYAML | https://pypi.org/project/PyYAML/ | MIT; installed separately for the helper |

中文：`TR3600-adaptation-sources.tar.gz` 包含用于适配的完整 Linux 和 OpenWrt 源码压缩包、上游库源码，以及配置、构建和打包说明。解压各上游压缩包可查看完整许可与版权声明。无需管理员口令或订阅即可下载源码。原厂运行内核分区镜像没有纳入分发。

English: `TR3600-adaptation-sources.tar.gz` contains the Linux and OpenWrt source archives used for adaptation, upstream library source, configuration and build/packaging instructions. Unpack each upstream archive for its full notices. Source downloads require no router credentials or subscription. The original vendor kernel-partition image is not redistributed.

中文：SHA256 用于确认本次归档字节，没有把自编包变成 OpenWrt 官方签名包，也不建立对其他固件的兼容承诺。重新分发或修改时应继续保留相关上游源码、配方与许可。

English: SHA256 values identify the archived bytes; they do not make the custom packages officially signed by OpenWrt or compatible with other firmware. Preserve relevant upstream source, recipes and notices when modifying or redistributing them.
