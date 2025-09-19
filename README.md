# 📺 M3U 直播源自动更新

[![M3U 直播源更新到 live.txt](https://github.com/qingtingjjjjjjj/IPTV-api/actions/workflows/update.yml/badge.svg)](https://github.com/qingtingjjjjjjj/IPTV-api/actions/workflows/update.yml)
[![Last Commit](https://img.shields.io/github/last-commit/qingtingjjjjjjj/IPTV-api)](https://github.com/qingtingjjjjjjj/IPTV-api/commits/main)
[![GitHub Stars](https://img.shields.io/github/stars/qingtingjjjjjjj/IPTV-api?style=social)](https://github.com/qingtingjjjjjjj/IPTV-api/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/qingtingjjjjjjj/IPTV-api?style=social)](https://github.com/qingtingjjjjjjj/IPTV-api/network/members)

---

本仓库会定时从远程地址抓取最新的 M3U 直播源，并更新到 `live.txt` 文件。  
通过 **GitHub Actions** 自动运行，无需人工维护。

---

## 🔄 更新逻辑

- **定时任务**：每 2 小时自动运行一次（也支持手动触发）。  
- **更新规则**：
  - 仅更新 **央视频道** 和 **卫视频道** 两个分组；
  - 每次抓取后覆盖掉上一次更新的源；
  - 保留组内其他手动添加的源；
  - 其他分组完全不变。  
- **异常处理**：
  - 如果远程抓取失败，将保留旧的 `live.txt`。

---

## 📂 文件说明

- `live.txt` ：最新的直播源文件（自动更新）。  
- `.github/workflows/update.yml` ：GitHub Actions 工作流配置文件。  
- `.github/workflows/update_live_txt.py` ：更新脚本（解析远程 M3U 并写入 `live.txt`）。  

---

## 🚀 手动运行

1. 打开仓库的 **Actions** 页面  
2. 选择 **M3U 直播源更新到 live.txt** 工作流  
3. 点击 **Run workflow** 即可立即触发更新任务  

---

## 🛠 技术说明

- 使用 `requests` 抓取远程 M3U 文件。  
- 自动分类频道：  
  - `央视频道,#genre#`  
  - `卫视频道,#genre#`  
- 日志中会输出本次新增频道数量与对应 URL。  

---

## ✨ 示例日志输出

## 📌 注意事项

- 本仓库仅供 **技术学习与交流** 使用。  
- 抓取到的源请勿用于任何商业用途。  

---

👏 欢迎 Star 本仓库，以便随时获取最新的直播源。

## 更新频率(北京时间)
|直播源|黑白名单|
| ---- | ---- |
|每日4点|每周五0点|


![telegram-cloud-photo-size-1-4902173344514813668-y](https://github.com/user-attachments/assets/3b641fd5-cb40-4d0d-abc7-7ffe4f494d88)

# 免责声明

> [!important]
>
> 1. 本仓库仅供学习使用，请尊重版权，请勿利用此仓库从事商业行为及非法用途!
> 2. 使用本仓库的过程中可能会产生版权数据。对于这些版权数据，本仓库不拥有它们的所有权。为了避免侵权，使用者务必在 24小时内清除使用本仓库的过程中所产生的版权数据。
> 3. 由于使用本仓库产生的包括由于本协议或由于使用或无法使用本仓库而引起的任何性质的任何直接、间接、特殊、偶然或结果性损害（包括但不限于因商誉损失、停工、计算机故障或故障引起的损害赔偿，或任何及所有其他商业损害或损失）由使用者负责。
> 4. **禁止在违反当地法律法规的情况下使用本仓库。** 对于使用者在明知或不知当地法律法规不允许的情况下使用本仓库所造成的任何违法违规行为由使用者承担，本仓库不承担由此造成的任何直接、间接、特殊、偶然或结果性责任。
> 5. 如果官方平台觉得本仓库不妥，可联系本仓库更改或移除。
