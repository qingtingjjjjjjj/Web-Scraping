import requests
import os
import re

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

live_file = "live.txt"
url = "https://raw.githubusercontent.com/develop202/migu_video/refs/heads/main/interface.txt"

# ===== 抓取远程 M3U =====
try:
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
except Exception as e:
    print(f"{RED}抓取失败，保留旧的 live.txt 文件: {e}{RESET}")
    exit(0)

lines = resp.text.splitlines()
yangshi, weishi = [], []

def simplify_name(name):
    match = re.match(r"(CCTV\d+)", name)
    if match:
        return match.group(1)
    return name

# 解析抓取内容
current_group, current_name = None, None
for line in lines:
    if line.startswith("#EXTINF"):
        current_name = line.split(",")[-1].strip()
        current_name = simplify_name(current_name)
        if "央视" in line:
            current_group = "yangshi"
        elif "卫视" in line:
            current_group = "weishi"
        else:
            current_group = None
    elif line.startswith("http") and current_group and current_name:
        record = f"{current_name},{line.strip()}"
        if current_group == "yangshi":
            yangshi.append(record)
        elif current_group == "weishi":
            weishi.append(record)

if not yangshi and not weishi:
    print(f"{RED}抓取到的直播源为空，保留旧的 live.txt 文件{RESET}")
    exit(0)

# ===== 读取原有 live.txt =====
if os.path.exists(live_file):
    with open(live_file, "r", encoding="utf-8") as f:
        old_lines = f.read().splitlines()
else:
    old_lines = []

# 分组标签
yangshi_tag = "央视频道,#genre#"
weishi_tag = "卫视频道,#genre#"

def update_group(existing_lines, tag, new_records):
    """在分组最前面插入新抓取源，删除上一次抓取源，保留其他源"""
    if tag not in existing_lines:
        return [tag] + new_records + [""] + existing_lines

    idx = existing_lines.index(tag) + 1
    end_idx = idx
    while end_idx < len(existing_lines) and existing_lines[end_idx].strip() != "" and not existing_lines[end_idx].endswith(",#genre#"):
        end_idx += 1

    group_lines = existing_lines[idx:end_idx]
    # 删除上一次抓取源（与新抓取源重叠的部分）
    filtered_group = [line for line in group_lines if line not in new_records]
    updated_group = new_records + filtered_group

    return existing_lines[:idx] + updated_group + existing_lines[end_idx:]

# ===== 更新两个分组 =====
lines_after_yangshi = update_group(old_lines, yangshi_tag, yangshi)
lines_after_weishi = update_group(lines_after_yangshi, weishi_tag, weishi)

# ===== 写回 live.txt =====
with open(live_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines_after_weishi))

# ===== 日志输出 =====
def log_channels(name, records, color):
    print(f"{color}新增{name}数量: {len(records)}{RESET}")
    for i, rec in enumerate(records, 1):
        channel_name = rec.split(',')[0]
        print(f"{color}{i}. {channel_name}{RESET}")

log_channels("央视频道", yangshi, GREEN)
log_channels("卫视频道", weishi, YELLOW)
print(f"{RED}更新完成，已覆盖上一次抓取的源，保留组内其他直播源和其他分组。{RESET}")
