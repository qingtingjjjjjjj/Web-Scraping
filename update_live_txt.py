import requests
import os
import re
import shutil
import time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===== 颜色定义（控制台日志）=====
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

live_file = "live.txt"
backup_dir = "backup"
marker_yangshi = "# LAST_UPDATE_YANGSHI"
marker_weishi = "# LAST_UPDATE_WEISHI"

# ===== 接口地址 =====
sources = {
    "TXT": "https://raw.githubusercontent.com/lucheng7996/TE/refs/heads/main/outfiles/beijing_cucc.txt",
    "M3U": "https://raw.githubusercontent.com/develop202/migu_video/refs/heads/main/interface.txt"
}

# ===== 工具函数 =====
def simplify_name(name: str) -> str:
    name = re.sub(r'HD', '', name, flags=re.IGNORECASE)
    name = re.sub(r'BRTV', '', name, flags=re.IGNORECASE)
    name = name.strip()
    cctv_match = re.match(r"CCTV[-]?(\d+)", name, re.IGNORECASE)
    if cctv_match:
        return f"CCTV{cctv_match.group(1)}"
    return name

def fetch_source(name, url, color, retries=3):
    for attempt in range(1, retries+1):
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            lines = resp.text.splitlines()
            print(f"{color}[{name}] 抓取成功，共 {len(lines)} 行{RESET}")
            return lines
        except Exception as e:
            print(f"{RED}[{name}] 第 {attempt} 次抓取失败: {e}{RESET}")
            time.sleep(1)
    return []

# ===== 初始化分组 =====
yangshi, weishi = [], []
yangshi_detail, weishi_detail = [], []

# ===== 并发抓取 M3U 和 TXT =====
start_time = time.time()
with ThreadPoolExecutor(max_workers=2) as executor:
    future_to_source = {
        executor.submit(fetch_source, name, url, BLUE if name=="TXT" else YELLOW): name
        for name, url in sources.items()
    }
    results = {}
    for future in as_completed(future_to_source):
        name = future_to_source[future]
        results[name] = future.result()

lines_m3u = results.get("M3U", [])
lines_txt = results.get("TXT", [])

# ===== 解析 M3U =====
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

# ===== 解析 TXT =====
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

# ===== 更新分组函数 =====
def update_group(existing_lines, new_records, marker):
    """
    删除上一次更新的源（标记行后面的内容），然后将本次新抓取放在前面
    """
    # 删除旧标记及其后面的内容
    if marker in existing_lines:
        idx = existing_lines.index(marker)
        end_idx = idx + 1
        while end_idx < len(existing_lines) and existing_lines[end_idx].strip() != "" and not existing_lines[end_idx].endswith("#genre#"):
            end_idx += 1
        existing_lines = existing_lines[:idx] + existing_lines[end_idx:]

    # 添加新内容和标记
    updated_lines = existing_lines + ["", marker] + new_records + [""]
    return updated_lines

# ===== 更新央视频道和卫视频道 =====
lines_after_yangshi = update_group(old_lines, yangshi, marker_yangshi)
lines_after_weishi = update_group(lines_after_yangshi, weishi, marker_weishi)

# ===== 备份 live.txt =====
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)
if os.path.exists(live_file):
    shutil.copy(live_file, os.path.join(backup_dir, f"live_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"))

# ===== 写回 live.txt =====
with open(live_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines_after_weishi))

# ===== 统计抓取数量 =====
txt_count = len(lines_txt)
m3u_count = len(lines_m3u)
total_count = len(lines_after_weishi)

# ===== 更新 README.md =====
beijing_tz = timezone(timedelta(hours=8))
timestamp = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")
header = f"## ✨于 {timestamp} 更新"
subline = f"**🎉最新可用IPTV源，TXT: {txt_count} 条，M3U: {m3u_count} 条，总计: {total_count} 条**"

def md_table(title, items, limit=5):
    """生成 Markdown 表格，每组只显示最新 limit 条"""
    if not items:
        return ""
    rows = "\n".join([f"| {rec.split(',')[0]} | {rec.split(',')[1]} |" for rec in items[:limit]])
    table = f"### {title}（只显示前 {limit} 条）\n\n| 频道名 | 链接 |\n| --- | --- |\n{rows}\n"
    return table

readme_update_lines = [
    header,
    subline,
    md_table("央视频道", yangshi, limit=5),
    md_table("卫视频道", weishi, limit=5),
    ""
]

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

    backup_file = os.path.join(backup_dir, f"README_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    shutil.copy("README.md", backup_file)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write("\n".join(readme_update_lines + new_readme))

# ===== 控制台日志 =====
def log_channels(name, records, detail_list, color):
    print(f"{color}{name}: 共 {len(records)} 条{RESET}")
    for i, rec in enumerate(detail_list, 1):
        print(f"{color}{i}. {rec}{RESET}")

log_channels("央视频道", yangshi, yangshi_detail, GREEN)
log_channels("卫视频道", weishi, weishi_detail, YELLOW)

end_time = time.time()
print(f"{RED}更新完成 ✅ 耗时 {end_time - start_time:.2f} 秒{RESET}")
print(f"{RED}live.txt 已更新，备份已保存到 {backup_dir}{RESET}")
