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
    "TXT": "https://hk.gh-proxy.com/https://raw.githubusercontent.com/AnonymousOrz/IPTV/main/Live/collect/央卫内地主流频道cs推流250824(4).txt",
    "M3U": "https://raw.githubusercontent.com/develop202/migu_video/refs/heads/main/interface.txt"
}

# ===== 工具函数 =====
def simplify_name(name: str) -> str:
    """清理频道名尾巴并修正 CCTV 编号"""
    tail_patterns = [r'HD', r'高清', r'HD高清', r'cs推流', r'推流cs', r'推流', r'cs', r'高码', r'BRTV']
    name = name.strip()
    changed = True
    while changed:
        changed = False
        for pattern in tail_patterns:
            if re.search(rf'{pattern}$', name, flags=re.IGNORECASE):
                name = re.sub(rf'{pattern}$', '', name, flags=re.IGNORECASE).strip()
                changed = True
    # CCTV 编号修正
    cctv_match = re.match(r"CCTV[-]?0*(\d+)", name, re.IGNORECASE)
    if cctv_match:
        return f"CCTV{cctv_match.group(1)}"
    return name

def fetch_source(name, url, color):
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        lines = resp.text.splitlines()
        print(f"{color}[{name}] 抓取成功，共 {len(lines)} 行{RESET}")
        return lines
    except Exception as e:
        print(f"{RED}[{name}] 抓取失败: {e}{RESET}")
        return []

# ===== 初始化分组 =====
yangshi, weishi = [], []
yangshi_detail, weishi_detail = [], []

# ===== 解析 TXT =====
lines_txt = fetch_source("TXT", sources["TXT"], GREEN)
for line in lines_txt:
    if not line or "," not in line:
        continue
    name, url = line.split(",", 1)
    name = simplify_name(name.strip())
    url = url.strip()
    if name.startswith("CCTV") or "央视" in name:
        yangshi.append(f"{name},{url}")
        yangshi_detail.append(f"{name} -> {url} (TXT)")
    elif "卫视" in name:
        weishi.append(f"{name},{url}")
        weishi_detail.append(f"{name} -> {url} (TXT)")

# ===== 解析 M3U =====
lines_m3u = fetch_source("M3U", sources["M3U"], YELLOW)
current_group, current_name = None, None
for line in lines_m3u:
    if line.startswith("#EXTINF"):
        current_name = simplify_name(line.split(",")[-1].strip())
        if "央视" in line or current_name.startswith("CCTV"):
            current_group = "yangshi"
        elif "卫视" in line:
            current_group = "weishi"
        else:
            current_group = None
    elif line.startswith("http") and current_group and current_name:
        record = f"{current_name},{line.strip()}"
        if current_group == "yangshi":
            yangshi.append(record)
            yangshi_detail.append(f"{current_name} -> {line.strip()} (M3U)")
        elif current_group == "weishi":
            weishi.append(record)
            weishi_detail.append(f"{current_name} -> {line.strip()} (M3U)")

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

def insert_group_front(existing_lines, tag, new_records):
    """插入新抓取源到分组前面，只保留最新抓取源，其他分组不变"""
    if tag not in existing_lines:
        return existing_lines + ["", tag] + new_records + [""]

    idx = existing_lines.index(tag) + 1
    end_idx = idx
    while end_idx < len(existing_lines) and existing_lines[end_idx].strip() != "" and not existing_lines[end_idx].endswith(",#genre#"):
        end_idx += 1

    # 删除旧源，只保留最新抓取的
    updated_group = new_records
    return existing_lines[:idx] + updated_group + existing_lines[end_idx:]

# ===== 更新分组 =====
lines_after_yangshi = insert_group_front(old_lines, yangshi_tag, yangshi)
lines_after_weishi = insert_group_front(lines_after_yangshi, weishi_tag, weishi)
lines_final = lines_after_weishi

# ===== 写回 live.txt =====
with open(live_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines_final))

# ===== 统计抓取数量 =====
txt_count = len(lines_txt)
m3u_count = len(lines_m3u)
total_count = len(lines_final)

# ===== 日志输出 =====
print("\n" + "="*50)
print(f"{GREEN}>>> TXT 本次抓取: {txt_count} 条源 {'➤'*3}{RESET}")
print(f"{BLUE}>>> M3U 本次抓取: {m3u_count} 条源 {'➤'*3}{RESET}")
print(f"{YELLOW}>>> 总计直播源: {total_count} 条 {'➤'*5}{RESET}")
print("="*50 + "\n")

# ===== 更新 README.md 时间戳 =====
beijing_tz = timezone(timedelta(hours=8))
timestamp = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")
header = f"## ✨于 {timestamp} 更新"
subline = f"**🎉最新可用IPTV源，TXT: {txt_count} 条，M3U: {m3u_count} 条，总计: {total_count} 条**"
statline = f"📺 当前共收录 {total_count} 条直播源"

if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as f:
        readme_lines = f.read().splitlines()
    new_readme = []
    skip_block = False
    for line in readme_lines:
        if line.startswith("## ✨于 "):
            skip_block = True
            continue
        if skip_block:
            if line.strip() == "" or line.startswith("## "):
                skip_block = False
            else:
                continue
        new_readme.append(line)
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
print(f"{RED}更新完成 ✅ 本次抓取的直播源已替换上一次，保留组内其他分组不变。{RESET}")
