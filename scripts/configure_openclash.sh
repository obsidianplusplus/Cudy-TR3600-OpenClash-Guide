#!/bin/sh
# Run on router AFTER installing packages and uploading the private YAML.
# 安装软件包、上传私人配置后，在路由器执行；本脚本保持 OpenClash 关闭。
set -eu
test -s /etc/openclash/config/Cudy-OpenClash.yaml
uci set openclash.config.enable='0'
uci set openclash.config.config_path='/etc/openclash/config/Cudy-OpenClash.yaml'
uci set openclash.config.en_mode='fake-ip-mix'
uci set openclash.config.operation_mode='fake-ip'
uci set openclash.config.proxy_mode='rule'
uci set openclash.config.core_type='Meta'
uci set openclash.config.stack_type='gvisor'
uci set openclash.config.enable_udp_proxy='1'
uci set openclash.config.disable_udp_quic='0'
uci set openclash.config.ipv6_enable='0'
uci set openclash.config.ipv6_dns='0'
uci set openclash.config.enable_custom_dns='0'
uci set openclash.config.enable_redirect_dns='1'
uci set openclash.config.redirect_dns='1'
uci set openclash.config.china_ip_route='1'
uci set openclash.config.china_ip6_route='0'
uci set openclash.config.enable_custom_clash_rules='0'
uci set openclash.config.rule_source='0'
uci set openclash.config.small_flash_memory='0'
uci set openclash.config.find_process_mode='off'
uci set openclash.config.router_self_proxy='1'
uci set openclash.config.intranet_allowed='1'
uci set openclash.config.log_level='0'
uci set openclash.config.fakeip_range='198.18.0.1/16'
uci set openclash.config.default_dashboard='metacubexd'
ruby -ryaml -e 'c=YAML.safe_load_file("/etc/openclash/config/Cudy-OpenClash.yaml", aliases: true); s=c.fetch("secret"); abort "empty secret" if s.to_s.empty?; abort unless system("uci", "set", "openclash.config.dashboard_password=#{s}")'
uci commit openclash
chmod 600 /etc/config/openclash /etc/openclash/config/Cudy-OpenClash.yaml
echo 'Configured but disabled / 配置已写入，尚未启用。Read activation + rollback steps in the tutorial.'
