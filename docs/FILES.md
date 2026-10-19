# 文件与校验值 / Files and checksums

[返回首页 / Back](../README.md)

## 1. 安装所需文件 / Required installation files

中文：固定版本与原始 SHA256 如下。两个自编 APK 从本仓库 Release 获取；官方应用与核心由下载脚本从官方 URL 获取。下载不需要任何私人订阅。

English: Versions and original digests are pinned below. Custom packages come from this release, while the application/core are downloaded from their official URLs. No private subscription is needed to download these artifacts.

### `kmod-tun-6.12.93-r100.apk`

- Size / 大小: `26,628` bytes
- SHA256: `80093e7ca9a4e690a2b18abca3ca9efac0a7bcd29803dbd0b23bbc456a01eeca`
- [Download / 下载](https://github.com/obsidianplusplus/Cudy-TR3600-OpenClash-Guide/releases/download/v1.0.0/kmod-tun-6.12.93-r100.apk)

### `libnetfilter-conntrack3-1.1.0-r100.apk`

- Size / 大小: `39,524` bytes
- SHA256: `04204ba3e93752868489c80bb1ca1840a81be73916682f4093f866ccba89c59d`
- [Download / 下载](https://github.com/obsidianplusplus/Cudy-TR3600-OpenClash-Guide/releases/download/v1.0.0/libnetfilter-conntrack3-1.1.0-r100.apk)

### `luci-app-openclash-0.48.002.apk`

- Size / 大小: `10,702,048` bytes
- SHA256: `f7ebbd43f9be15c5e6df26e5d0c03d50d0bb8f7fa4cc0d2c2bf048b08c0b155b`
- [Download / 下载](https://github.com/vernesong/OpenClash/releases/download/v0.48.002/luci-app-openclash-0.48.002.apk)

### `mihomo-linux-arm64-v1.19.32.gz`

- Size / 大小: `20,809,592` bytes
- SHA256: `9dd862e28b46ff7d775f169cceebc28deccaa0a9e804237d421cd2571e0caba0`
- [Download / 下载](https://github.com/MetaCubeX/mihomo/releases/download/v1.19.32/mihomo-linux-arm64-v1.19.32.gz)

### `TR3600-adaptation-sources.tar.gz`

- Size / 大小: `160,447,844` bytes
- SHA256: `20b234b9a00a982b6710b7f1e94cce9400f1cf062f17595312d8239a4174777f`
- [Download / 下载](https://github.com/obsidianplusplus/Cudy-TR3600-OpenClash-Guide/releases/download/v1.0.0/TR3600-adaptation-sources.tar.gz)

## 2. 源码归档的内容 / Source archive contents

中文：源码包包括以下固定输入，不含私人配置和原厂内核分区镜像。安装 OpenClash 不需要先编译源码；它用于核对、修改和重建适配模块。

English: The source archive contains the pinned inputs below, without private configuration or the vendor kernel-partition image. Compilation is not required to install the recorded artifacts; source is provided for inspection and rebuilding.

| Source / 源码 | SHA256 |
|---|---|
| Linux 6.12.93 | `492648a87c0b69c5ac7f43be64792b9000e3439550d4e82e4a14710c49094fa3` |
| Archived OpenWrt c484731c5a | `c2e7c67da0ac2e0339e5a7861f27ed4d05f41eb0dd9dbdf521f97cb021989ccf` |
| libnetfilter_conntrack 1.1.0 | `67edcb4eb826c2f8dc98af08dabff68f3b3d0fe6fb7d9d0ac1ee7ecce0fe694e` |

## 3. 手工校验 / Manual verification

```sh
# macOS
shasum -a 256 packages/*.apk packages/*.gz
# Linux / OpenWrt
sha256sum packages/*.apk packages/*.gz
```

中文：自动下载器会直接比较完整 SHA256。仓库根目录 `SHA256SUMS` 校验教程、示例、脚本和编译配置；Release 的 `SHA256SUMS` 校验其下载资产。校验失败时不要安装。

English: The downloader compares complete SHA256 values automatically. Root `SHA256SUMS` covers repository documentation, examples, scripts and build inputs; the release checksum file covers release assets. Do not install a mismatching download.

## 4. 本地与公开文件的区别 / Local versus public files

中文：完整路由器配置备份只保存在本地私人目录；它可能含管理员认证、无线口令和订阅。GitHub 发布页不提供这些文件。先前准备但没有刷入的候选固件不属于本次成功方案，也未纳入发布。

English: Full router backups remain private and local because they can contain administrator authentication, wireless keys and subscriptions. They are not release assets. Previously considered but unflashed candidate firmware is outside the successful procedure and is excluded.

中文：四个主要安装文件仍需软件源中的用户态依赖，不应称为完全离线安装套件。若要离线重装，另行归档 APK 求解的依赖，并确保其版本属于目标固件。

English: The four main installation files still require feed-provided userspace dependencies. They are not a complete offline installer; archive the resolved matching dependencies separately for offline reinstallation.
