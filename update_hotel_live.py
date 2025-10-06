import requests
import os

# 配置
SOURCE_URL = "https://raw.githubusercontent.com/wangchongzhq/wangchongzhq/2dbe3356a5a073fa4981f54c6b6e53e9117ca10e/109.txt"
OUTPUT_FILE = "live.txt"
GROUP_KEYWORD = "🇨🇳 4K"
TARGET_INSERT_KEYWORD = "央视频道,#genre#"

# 获取源文件
def fetch_source(url):
    try:
        resp = requests.get(url, timeout=15)
        resp.encoding = 'utf-8'
        return resp.text
    except Exception as e:
        print(f"❌ 获取源失败: {e}")
        return ""

# 提取指定分组
def extract_group(content, group_keyword):
    lines = content.splitlines()
    result = []
    include_line = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line == f"{group_keyword},#genre#":
            include_line = True
            result.append(line)
            continue
        if include_line:
            if ",#genre#" in line and group_keyword not in line:
                break
            parts = line.split(",", 1)
            if len(parts) == 2:
                result.append(f"{parts[0]}: {parts[1]}")
    return result

# 插入分组到目标位置
def insert_group_into_file(file_path, group_lines, target_keyword):
    if not os.path.exists(file_path):
        print(f"⚠️ 文件 {file_path} 不存在，将创建新文件。")
        existing_lines = []
    else:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            existing_lines = f.read().splitlines()

    new_lines = []
    inserted = False
    for line in existing_lines:
        if not inserted and target_keyword in line:
            new_lines.extend(group_lines)
            inserted = True
        new_lines.append(line)

    if not inserted:
        # 如果找不到目标位置，就追加到末尾
        new_lines.extend(group_lines)

    with open(file_path, "w", encoding="utf-8-sig") as f:
        for line in new_lines:
            f.write(line + "\n")
    print(f"✅ 分组已插入到 {file_path}")

# 主函数
def main():
    content = fetch_source(SOURCE_URL)
    if not content:
        return

    group_lines = extract_group(content, GROUP_KEYWORD)
    if not group_lines:
        print(f"⚠️ 没有抓取到 {GROUP_KEYWORD} 分组内容")
        return

    insert_group_into_file(OUTPUT_FILE, group_lines, TARGET_INSERT_KEYWORD)
    print(f"总计 {len([l for l in group_lines if 'http' in l])} 个直播源已插入 {GROUP_KEYWORD} 分组。")

if __name__ == "__main__":
    main()
