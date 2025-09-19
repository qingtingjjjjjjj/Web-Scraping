import requests
import os
import re

# 抓取 M3U
url = "https://raw.githubusercontent.com/develop202/migu_video/refs/heads/main/interface.txt"
resp = requests.get(url)
resp.raise_for_status()
lines = resp.text.splitlines()

# 分组
yangshi, weishi = [], []
current_group = None
current_name = None

# CCTV 统一简化规则
def simplify_name(name):
    match = re.match(r"(CCTV\d+)", name)
    if match:
        return match.group(1)
    return name

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

# live.txt 文件路径
live_file = "live.txt"
if os.path.exists(live_file):
    with open(live_file, "r", encoding="utf-8") as f:
        old_lines = f.read().splitlines()
else:
    old_lines = []

# 定义分组标签
yangshi_tag = "央视频道,#genre#"
weishi_tag = "卫视频道,#genre#"

# 将已有直播源收集到 set 中（用于去重）
existing_set = set(old_lines)

# 去掉已经存在的直播源
yangshi_new = [x for x in yangshi if x not in existing_set]
weishi_new = [x for x in weishi if x not in existing_set]

# 找到分组起始位置并插入新直播源
def insert_group(existing_lines, tag, new_records):
    if not new_records:
        return existing_lines
    if tag in existing_lines:
        idx = existing_lines.index(tag) + 1
        # 插入到分组最前面，保持抓取顺序
        return existing_lines[:idx] + new_records + existing_lines[idx:]
    else:
        # 分组不存在，创建新分组放在文件最前面
        return [tag] + new_records + [""] + existing_lines

# 插入央视频道和卫视频道
lines_after_yangshi = insert_group(old_lines, yangshi_tag, yangshi_new)
lines_after_weishi = insert_group(lines_after_yangshi, weishi_tag, weishi_new)

# 写回 live.txt
with open(live_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines_after_weishi))

print(f"新增央视频道数量: {len(yangshi_new)}")
print(f"新增卫视频道数量: {len(weishi_new)}")
print("更新完成，已插入到对应分组最前面（保持顺序且去重）。")
