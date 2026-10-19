# 内核适配原理与编译记录 / Kernel adaptation and build record

[返回首页 / Back](../README.md)

## 1. 为什么仅降级插件不能解决 / Why a plugin downgrade is insufficient

中文：LuCI 是管理界面，Mihomo 是用户态代理核心，TUN 则是 Linux 内核驱动。前两者可以作为普通软件包或二进制更新；缺少的内核能力必须由兼容模块或内核本身提供。OpenWrt 的 kernel 包依赖还包含配置校验值。不同构建即便都叫 Linux 6.12.93，也可能有不同模块结构和导出符号。

English: LuCI is the management application, Mihomo a userspace proxy core, and TUN a Linux driver. Updating the first two does not create a missing kernel facility. OpenWrt kernel dependencies also encode a configuration hash. Two kernels labelled 6.12.93 can still differ in module structures and exported symbols.

中文：本次成功的关键不是修改版本号，而是重建原配置、核对配置输入校验值、编译真正模块，再在实机验证加载与数据流。ABI hash 匹配是重要检查，但仍不是“所有模块必定兼容”的充分证明。

English: The successful approach reconstructed the configuration, matched its input hash, built a real module, and validated both loading and traffic on the device. Matching the ABI hash is an important check, not a universal proof of module compatibility.

## 2. 收集设备证据 / Collect evidence from the router

```sh
# Router / 路由器, read-only
ubus call system board
uname -a
apk info -v kernel
apk info -v | sed -n '/^kmod-/p'
lsmod
cat /proc/kallsyms > /tmp/router-kallsyms.txt
```

中文：本次精确 kernel 版本为 `6.12.93~f67f61bf2367ca6002566e9da365b1b8-r1`。原镜像不提供可直接提取的 IKCONFIG，也没有可用于这一步的 BTF；因此使用实际已安装 kmod 清单和对应 OpenWrt 源码重建配置。读取启动内核分区仅用于离线核对，没有写入分区；原镜像和原始运行内存符号表不作为公开安装资产分发。

English: The exact dependency was `6.12.93~f67f61bf2367ca6002566e9da365b1b8-r1`. The original image did not expose an extractable IKCONFIG or usable BTF for this task. Configuration was reconstructed using the installed kmod inventory and matching OpenWrt source. Kernel-partition reads were for offline inspection only; no partition was written. The vendor image and raw runtime symbol dump are not distributed as installation assets.

## 3. 已归档的输入 / Archived inputs

| 文件 / File | 用途 / Purpose |
|---|---|
| `build/router-kmods.txt` | Installed kmod inventory / 原 kmod 清单 |
| `build/openwrt-config.seed` | OpenWrt metadata selection seed / 元数据选择种子 |
| `build/kernel-original-config.set` | Merged configuration input matching original hash / 原校验匹配输入 |
| `build/kernel-baseline-resolved.config` | Baseline after Kconfig resolution / 解析后的原配置 |
| `build/kernel-adapted-config` | Actual complete build configuration / 实际编译配置 |
| `build/Module.symvers` | Export information from this build / 本次构建的导出信息 |

中文：Release 的 `TR3600-adaptation-sources.tar.gz` 同时提供 Linux 6.12.93、OpenWrt 对应源码快照、libnetfilter_conntrack 1.1.0 上游源码，以及本仓库的构建配方和配置副本。源码与二进制保留各自许可。

English: The release source archive includes Linux 6.12.93, the matching OpenWrt snapshot, upstream libnetfilter_conntrack 1.1.0, and copies of the build recipes/configuration. Upstream licenses remain attached to source and binaries.

## 4. 隔离构建环境 / Isolated build environment

中文：实际使用 Apple Silicon Mac 上的 Lima 2.2.1，ARM64 Alpine 3.23.4，4 CPU、4 GiB 内存、20 GiB 磁盘，原生 GCC 15.2.0。原固件使用 GCC 14.3.0。本文不宣称位级可复现；日期、工具链、构建用户名等也会影响二进制。重建后应重新验证，不能用“编译成功”替代设备验证。

English: The actual environment was Lima 2.2.1 on Apple Silicon, running ARM64 Alpine 3.23.4 with four CPUs, 4 GiB RAM, 20 GiB disk and native GCC 15.2.0. The vendor used GCC 14.3.0. This is not a bit-for-bit reproducibility claim: toolchain and build metadata affect output. Rebuilds require renewed device validation.

中文：Lima 可从 [官方 2.2.1 发布页](https://github.com/lima-vm/lima/releases/tag/v2.2.1) 获取。虚拟机目录可用 `/tmp/tr3600-lima`，避免过长路径触及 Unix socket 长度限制。创建 ARM64 Alpine 虚拟机；若默认用户态网络不可用，可在 Lima 支持范围内使用 VZ NAT。以下构建命令全部在 **ARM64 Linux 虚拟机内**执行，不在 macOS 直接执行。

English: Obtain Lima from its [official release](https://github.com/lima-vm/lima/releases/tag/v2.2.1). A short VM-state path such as `/tmp/tr3600-lima` avoids Unix-socket path limits. Create an ARM64 Alpine guest; VZ NAT was used when default userspace networking was unreliable. The commands below run **inside ARM64 Linux**, not directly on macOS.

```sh
# ARM64 Alpine guest / ARM64 Alpine 虚拟机
sudo apk add build-base bash perl python3 git patch diffutils gawk grep sed \
  findutils tar xz bison flex ncurses-dev zlib-dev openssl-dev elfutils-dev \
  rsync file curl wget coreutils linux-headers gzip unzip bzip2 \
  argp-standalone musl-fts-dev musl-obstack-dev gettext-dev kmod
```

## 5. 校验并解压源码 / Verify and extract source

中文：源码 SHA256 见 [文件清单](FILES.md)。将源码与本仓库复制进构建目录。下面假定 `guide/` 为本仓库，两个源码压缩包在当前目录。OpenWrt 压缩包只使用已归档版本，避免 GitHub 重新生成 tar 流时出现压缩层哈希差异。

English: Verify checksums from the [file list](FILES.md). Copy the source archives and repository into the build directory. These examples assume `guide/` contains this repository and archives are in the current directory. Prefer the archived OpenWrt tarball because regenerated archives can differ at the compressed-byte level.

```sh
mkdir -p src kernel
tar -xzf openwrt-c484731c5a.tar.gz --strip-components=1 -C src
tar -xJf linux-6.12.93.tar.xz --strip-components=1 -C kernel
```

## 6. 重建原始配置输入 / Reconstruct the original configuration input

中文：这一步解释归档配置如何得到。先使用种子生成 OpenWrt 的 `.config` 和包元数据，再将 generic、filogic、CONFIG_KERNEL 以及包的内核选项合并。种子中的 `cudy_tr3000-v1` 是用于此公开源码树的元数据选择项；**本次没有用它生成 TR3600 固件，也不能把它当作刷机 profile**。实际硬件兼容性依据是平台、配置、符号与加载验证。

English: This explains how the archived input was produced. Generate OpenWrt `.config` and package metadata, then merge generic, filogic, CONFIG_KERNEL and package kernel options. The seed's `cudy_tr3000-v1` selection was used for metadata in this public tree; **it was not used to build firmware for TR3600 and is not a flashing profile**. Compatibility was assessed through target, configuration, symbols and actual loading.

```sh
cp guide/build/openwrt-config.seed src/.config
(cd src && make defconfig)
mkdir -p reconstructed
src/scripts/kconfig.pl + src/target/linux/generic/config-6.12 \
  src/target/linux/mediatek/filogic/config-6.12 > reconstructed/config.target
awk '/^(#[[:space:]]+)?CONFIG_KERNEL/{sub("CONFIG_KERNEL_","CONFIG_");print}' \
  src/.config >> reconstructed/config.target
printf '%s\n' '# CONFIG_KALLSYMS_EXTRA_PASS is not set' \
  '# CONFIG_KALLSYMS_ALL is not set' 'CONFIG_KALLSYMS_UNCOMPRESSED=y' \
  >> reconstructed/config.target
src/scripts/package-metadata.pl kconfig src/tmp/.packageinfo src/.config 6.12 \
  > reconstructed/config.override
src/scripts/kconfig.pl m+ + reconstructed/config.target /dev/null \
  reconstructed/config.override > reconstructed/config.set
grep '=[ym]' reconstructed/config.set | LC_ALL=C sort | md5sum
```

中文：本次结果必须是 `f67f61bf2367ca6002566e9da365b1b8`。`kernel-original-config.set` 就是归档的输入。它包含合并过程中尚未由 Kconfig 消解的选项，所以不要把它当作已解析的内核 `.config`；接下来要运行 `olddefconfig`。如果重新生成结果不同，应比较源码和包选择，不能手动改 hash 让它“通过”。

English: The observed result was `f67f61bf2367ca6002566e9da365b1b8`. The archived `kernel-original-config.set` is this merged input. It can contain options not yet reconciled by Kconfig, so run `olddefconfig` before compiling. A differing regenerated hash requires investigating source/package selection, not editing the hash.

## 7. 应用 OpenWrt 源码和补丁 / Apply OpenWrt files and patches

```sh
for directory in \
  src/target/linux/generic/files \
  src/target/linux/generic/files-6.12 \
  src/target/linux/mediatek/files \
  src/target/linux/mediatek/files-6.12; do
  if [ -d "$directory" ]; then cp -a "$directory/." kernel/; fi
done

for directory in \
  src/target/linux/generic/backport-6.12 \
  src/target/linux/generic/pending-6.12 \
  src/target/linux/generic/hack-6.12 \
  src/target/linux/mediatek/patches-6.12; do
  sh src/scripts/patch-kernel.sh kernel "$directory"
done

grep -v INITRAMFS guide/build/kernel-original-config.set > kernel/.config
printf '%s\n' 'CONFIG_INITRAMFS_SOURCE=""' \
  '# CONFIG_INITRAMFS_FORCE is not set' \
  '# CONFIG_INITRAMFS_PRESERVE_MTIME is not set' >> kernel/.config
(cd kernel && make ARCH=arm64 olddefconfig)
cp kernel/.config kernel/.config.baseline
```

中文：任何补丁失败都应停止并核对版本和顺序。板级 DTS 与启动参数补丁不是本次单独编译 TUN 所需的部分；不能据此认为这里可以构建可刷写的完整 TR3600 镜像。

English: Stop on any patch failure and check versions/order. Board DTS and vendor boot-parameter work were unnecessary for this standalone TUN task. This procedure is not a recipe for producing flashable TR3600 firmware.

## 8. 启用模块与编译 / Enable modules and compile

中文：本次探索同时编译了 TUN 与三个 TPROXY 候选模块，最终只安装 TUN。要复核同一构建配置，可将归档的完整 `kernel-adapted-config` 用作 `.config`；或者在解析后的基线上只增加以下四项。确认没有顺带打开 INET_DIAG/SOCK_DIAG 等新内建能力。

English: The exploratory build enabled TUN plus three TPROXY candidates; only TUN was installed. Use the archived complete adapted configuration to reproduce the selected configuration, or enable the four modules below on the resolved baseline. Ensure no additional built-in INET_DIAG/SOCK_DIAG facilities are enabled inadvertently.

```sh
(cd kernel && scripts/config --module TUN \
  --module NF_TPROXY_IPV4 --module NF_TPROXY_IPV6 --module NFT_TPROXY)
(cd kernel && make ARCH=arm64 olddefconfig)
(cd kernel && scripts/diffconfig .config.baseline .config)
(cd kernel && make ARCH=arm64 -j4 vmlinux modules)
```

中文：编译 `vmlinux` 是为了完整生成构建依赖和导出信息，**这个文件没有写入路由器**。只复制本次构建的 `drivers/net/tun.ko` 用于后续检查。构建输出的原始模块 SHA256 为 `9c00f0352cfbdc302fd190d10342696d39634681aca3c7e27adbf443d28a7353`，约 67 KiB；不同构建环境可能得到不同字节。

English: Building `vmlinux` generated the required build dependencies and export information; **it was never installed on the router**. Only `drivers/net/tun.ko` proceeded to deployment checks. The original build produced a roughly 67 KiB module with SHA256 `9c00f0352cfbdc302fd190d10342696d39634681aca3c7e27adbf443d28a7353`. Different environments can change the bytes.

## 9. ABI 与实际能力检查 / ABI and capability checks

```sh
# Linux build guest / Linux 构建虚拟机
modinfo kernel/drivers/net/tun.ko
readelf -sW kernel/drivers/net/tun.ko | grep __this_module
nm -u kernel/drivers/net/tun.ko
```

中文：本次 vermagic 为 `6.12.93 SMP mod_unload aarch64`，模块描述结构大小与原设备已有模块比较为 `0x2c0`。未定义符号需要逐项确认由当前内核或已加载依赖提供；`/proc/kallsyms` 未开启 ALL 时可能不显示部分数据符号，不能简单把文本差集当成最终兼容结论。最终仍需不带强制选项的实机加载和真实网络测试。

English: The observed vermagic was `6.12.93 SMP mod_unload aarch64`; the module descriptor size matched an existing vendor module at `0x2c0`. Check undefined references against kernel and loaded dependencies. With KALLSYMS_ALL disabled, some data symbols are not listed, so a textual difference alone is inconclusive. The final checks are unforced loading and real traffic tests.

中文：三个 TPROXY 候选缺少原内核导出的 UDP lookup helper，因此没有安装或持久化。为了 conntrack-netlink 直接替换原 nf_conntrack 也不合适：原配置未启用连接事件，新增能力可能影响现有模块 ABI。最终选择当前内核可支持的混合模式，而没有替换原网络核心模块。

English: The TPROXY candidates needed UDP lookup helpers not exported by the running kernel, so they were not installed or persisted. Replacing nf_conntrack for netlink support was also inappropriate because enabling absent connection-event facilities could alter ABI assumptions. The verified mixed mode avoided replacing those core networking modules.

## 10. TUN APK 的包装 / Packaging the TUN APK

中文：在支持 `apk mkpkg` 的 APK 3.0.6 构建环境中执行，使用 `--compat 3.0.0` 与路由器 APK 3.0.5 兼容。打包目录应为 root:root 所有，可在隔离虚拟机内使用 sudo 执行下列步骤。打包前不要把私钥、日志或其他模块放进 stage。

English: Use APK 3.0.6 with `apk mkpkg` and `--compat 3.0.0` for the router's APK 3.0.5. Staged files must be root-owned; perform ownership operations inside the isolated guest. Keep keys, logs and unrelated modules out of the stage.

```sh
mkdir -p stage-tun/lib/modules/6.12.93 stage-tun/etc/modules.d stage-tun/lib/apk/packages
cp kernel/drivers/net/tun.ko stage-tun/lib/modules/6.12.93/tun.ko
printf 'tun\n' > stage-tun/etc/modules.d/30-tun
printf '%s\n' /lib/modules/6.12.93/tun.ko /etc/modules.d/30-tun \
  > stage-tun/lib/apk/packages/kmod-tun.list
sudo chown -R root:root stage-tun
sudo apk mkpkg --compat 3.0.0 \
  --info 'name:kmod-tun' --info 'version:6.12.93-r100' \
  --info 'arch:aarch64_cortex-a53' --info 'license:GPL-2.0-only' \
  --info 'description:TUN driver adapted for the recorded TR3600 kernel' \
  --info 'depends:kernel=6.12.93~f67f61bf2367ca6002566e9da365b1b8-r1' \
  --files stage-tun --output kmod-tun-6.12.93-r100.apk
```

中文：重打包命令展示结构与精确依赖；构建元数据不同会使 APK 哈希不同。Release 内的 APK 是实际安装过的原产物，其固定校验值见清单。

English: This recipe documents file layout and the exact dependency. Metadata changes affect the APK digest. The release APK is the original installed artifact with its own recorded checksum.

## 11. 用户态 conntrack 库的重打包 / Repackaging the userspace conntrack library

中文：使用官方 `libnetfilter-conntrack3` 1.1.0-r1 原包解出文件，保留 ELF 字节与 soname，增加版本后缀 r100，保留 libc/libmnl/libnfnetlink 依赖，仅移除不可满足的内核 netlink 模块依赖。重打包前后应比较所有库文件 SHA256。

English: Extract the official 1.1.0-r1 package, retain its ELF bytes and soname, assign release r100, and keep libc/libmnl/libnfnetlink dependencies. Remove only the unavailable kernel netlink dependency. Compare library checksums before and after packaging.

```sh
mkdir -p stage-conntrack
apk extract --allow-untrusted --destination stage-conntrack \
  libnetfilter-conntrack3-official.apk
find stage-conntrack/usr/lib -type f -exec sha256sum '{}' \;
sudo chown -R root:root stage-conntrack
sudo apk mkpkg --compat 3.0.0 \
  --info 'name:libnetfilter-conntrack3' --info 'version:1.1.0-r100' \
  --info 'arch:aarch64_cortex-a53' --info 'license:GPL-2.0-or-later' \
  --info 'description:Unmodified userspace library; kernel netlink feature not supplied' \
  --info 'depends:libc libmnl0 libnfnetlink0' \
  --info 'provides:libnetfilter-conntrack libnetfilter-conntrack-any' \
  --files stage-conntrack --output libnetfilter-conntrack3-1.1.0-r100.apk
```

中文：APK 工具如果无法识别子命令，核对构建环境的 APK 版本与 `apk mkpkg --help`，不要把旧式 `.ipk` 改名当 `.apk`。该包不实现缺失的内核功能；启用 dnsmasq 的 conntrack 查询或安装 conntrack 工具前必须重新评估依赖。

English: If the subcommand is unavailable, verify the build tool version and `apk mkpkg --help`; renaming an IPK to APK is not conversion. This package does not implement the missing kernel facility. Reassess dependencies before enabling dnsmasq conntrack queries or adding tools that need that API.

## 12. 部署与验证边界 / Deployment and validation boundaries

中文：只把已核对的 TUN 包和用户态适配包用于首页指定设备；部署步骤、回退计时和真实 TCP/UDP 测试见主教程。公开配置生成器与回退脚本在整理文档时做了语法和离线功能检查，但没有再次在运行路由器上重装整个系统。原始实机结果与公开辅助脚本测试在验证章节分别列明。

English: Deploy only to the exact recorded target after checks, following the main tutorial's rollback and TCP/UDP validation. Public helper scripts received syntax and offline functional checks during documentation work; the complete installation was not repeated on the running router just to publish the guide. Device results and helper validation are listed separately.
