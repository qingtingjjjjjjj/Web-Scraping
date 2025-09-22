import requests
import os
import re
from datetime import datetime, timedelta, timezone

# ===== 颜色定义 =====
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

live_file = "live.txt"

# ===== 接口地址 =====
sources = {
    "M3U": "https://raw.githubusercontent.com/develop202/migu_video/refs/heads/main/interface.txt",
    "TXT": "https://raw.githubusercontent.com/cnliux/cnliux.github.io/refs/heads/main/tv.txt"
}

# ===== 工具函数 =====
def simplify_name(name: str) -> str:
    """清理频道名：去掉 HD/BRTV，CCTV 特殊处理"""
    name = re.sub(r'HD', '', name, flags=re.IGNORECASE)
    name = re.sub(r'BRTV', '', name, flags=re.IGNORECASE)
    name = name.strip()
    cctv_match = re.match(r"CCTV[-]?(\d+)", name, re.IGNORECASE)
    if cctv_match:
        return f"CCTV{cctv_match.group(1)}"
    return name

def fetch_source(name, url, color):
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        lines = resp.text.splitlines()
        print(f"{color}[{name}] 抓取成功，共 {len(lines)} 行{RESET}")
        return lines
    except Exception as e:
        print(f"{RED}[{name}] 抓取失败: {e}{RESET}")
        return []

# ===== 初始化分组 =====
yangshi, weishi = [], []
yangshi_detail, weishi_detail = [], []

# ===== 解析 M3U =====
lines_m3u = fetch_source("M3U", sources["M3U"], YELLOW)
current_group, current_name = None, None
for line in lines_m3u:
    if line.startswith("#EXTINF"):
        # EXTINF 行通常形如: #EXTINF:-1,频道名（或包含“央视/卫视”等关键字）
        current_name = simplify_name(line.split(",")[-1].strip())
        if "央视" in line or current_name.upper().startswith("CCTV"):
            current_group = "yangshi"
        elif "卫视" in line:
            current_group = "weishi"
        else:
            current_group = None
    else:
        # 支持多种流地址协议：http, https, udp, rtmp, rtsp
        if re.match(r'^(https?://|udp://|rtmp://|rtsp://)', line.strip(), re.IGNORECASE) and current_group and current_name:
            record = f"{current_name},{line.strip()}"
            if current_group == "yangshi":
                yangshi.append(record)
                yangshi_detail.append(f"{current_name} -> {line.strip()} (M3U)")
            elif current_group == "weishi":
                weishi.append(record)
                weishi_detail.append(f"{current_name} -> {line.strip()} (M3U)")

# ===== 解析 TXT =====
lines_txt = fetch_source("TXT", sources["TXT"], BLUE)
for line in lines_txt:
    if "," in line:
        name, url = line.split(",", 1)
        name = simplify_name(name)
        record = f"{name},{url.strip()}"
        if "CCTV" in name:
            yangshi.append(record)
            yangshi_detail.append(f"{name} -> {url.strip()} (TXT)")
        elif "卫视" in name:
            weishi.append(record)
            weishi_detail.append(f"{name} -> {url.strip()} (TXT)")

if not yangshi and not weishi:
    print(f"{RED}抓取到的直播源为空，保留旧的 live.txt 文件{RESET}")
    exit(0)

# ===== 读取原有 live.txt =====
if os.path.exists(live_file):
    with open(live_file, "r", encoding="utf-8") as f:
        old_lines = f.read().splitlines()
else:
    old_lines = []

# ===== 分组标签 =====
yangshi_tag = "央视频道,#genre#"
weishi_tag = "卫视频道,#genre#"

def update_group(existing_lines, tag, new_records):
    """覆盖上一次抓取内容，保留组内其他旧直播源"""
    if not new_records:
        return existing_lines

    if tag not in existing_lines:
        return existing_lines + ["", tag] + new_records + [""]

    idx = existing_lines.index(tag) + 1
    end_idx = idx
    while end_idx < len(existing_lines) and existing_lines[end_idx].strip() != "" and not existing_lines[end_idx].endswith(",#genre#"):
        end_idx += 1

    # 当前组旧行
    old_group_lines = existing_lines[idx:end_idx]
    # 新抓取的名称集合
    new_names = {rec.split(",")[0] for rec in new_records}
    # 保留旧行中不在新抓取列表的
    filtered_old_lines = [line for line in old_group_lines if line.split(",")[0] not in new_names]

    # 新抓取内容在前，旧未更新内容在后
    updated_group = new_records + filtered_old_lines

    return existing_lines[:idx] + updated_group + existing_lines[end_idx:]

# ===== 更新分组 =====
lines_after_yangshi = update_group(old_lines, yangshi_tag, yangshi)
lines_after_weishi = update_group(lines_after_yangshi, weishi_tag, weishi)

# ===== 写回 live.txt =====
with open(live_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines_after_weishi))

# ===== 统计抓取数量 =====
m3u_count = len(lines_m3u)
txt_count = len(lines_txt)
total_count = len(lines_after_weishi)

# ===== 颜色化仪表盘日志 =====
print("\n" + "="*50)
print(f"{YELLOW}>>> M3U 本次抓取: {m3u_count} 条源 {'➤'*3}{RESET}")
print(f"{BLUE}>>> TXT 本次抓取: {txt_count} 条源 {'➤'*3}{RESET}")
print(f"{GREEN}>>> 总计直播源: {total_count} 条 {'➤'*5}{RESET}")
print("="*50 + "\n")

# ===== 更新 README.md 时间戳和统计 =====
beijing_tz = timezone(timedelta(hours=8))
timestamp = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")

header = f"## ✨于 {timestamp} 更新"
subline = f"**🎉最新可用IPTV源，M3U: {m3u_count} 条，TXT: {txt_count} 条，总计: {total_count} 条**"
statline = f"📺 当前共收录 {total_count} 条直播源"

if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as f:
        readme_lines = f.read().splitlines()

    # 删除旧时间戳块
    new_readme = []
    skip_block = False
    for line in readme_lines:
        if line.startswith("## ✨于 "):
            skip_block = True
            continue
        if skip_block:
            # 结束条件：遇到空行或下一段标题
            if line.strip() == "" or line.startswith("## "):
                skip_block = False
            else:
                continue
        new_readme.append(line)

    # 插入新的时间戳和统计信息
    readme_content = "\n".join([header, subline, statline, ""] + new_readme)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

# ===== 日志输出频道详细信息 =====
def log_channels(name, records, detail_list, color):
    print(f"{color}{name}: 新增 {len(records)} 条{RESET}")
    for i, rec in enumerate(detail_list, 1):
        print(f"{color}{i}. {rec}{RESET}")

log_channels("央视频道", yangshi, yangshi_detail, GREEN)
log_channels("卫视频道", weishi, weishi_detail, YELLOW)
print(f"{RED}更新完成 ✅ 已覆盖上一次抓取内容，保留组内其他直播源和其他分组。{RESET}")
