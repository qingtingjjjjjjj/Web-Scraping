import requests
import os

# 配置
SOURCE_URL = "https://raw.githubusercontent.com/wangchongzhq/wangchongzhq/2dbe3356a5a073fa4981f54c6b6e53e9117ca10e/109.txt"
OUTPUT_FILE = "live.txt"
GROUP_KEYWORD = "🇨🇳 4K"

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

# 插入分组到文件开头
def insert_group_at_top(file_path, group_lines):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8-sig") as f:
            existing_lines = f.read().splitlines()
    else:
        existing_lines = []

    new_lines = group_lines + existing_lines

    with open(file_path, "w", encoding="utf-8-sig") as f:
        for line in new_lines:
            f.write(line + "\n")
    print(f"✅ 分组已插入到 {file_path} 开头")

# 主函数
def main():
    content = fetch_source(SOURCE_URL)
    if not content:
        return

    group_lines = extract_group(content, GROUP_KEYWORD)
    if not group_lines:
        print(f"⚠️ 没有抓取到 {GROUP_KEYWORD} 分组内容")
        return

    print(f"抓取到 {len(group_lines)} 行 {GROUP_KEYWORD} 分组内容")

    insert_group_at_top(OUTPUT_FILE, group_lines)
    print(f"总计 {len([l for l in group_lines if 'http' in l])} 个直播源已插入 {GROUP_KEYWORD} 分组。")

if __name__ == "__main__":
    main()
