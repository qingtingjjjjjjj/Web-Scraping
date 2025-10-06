import requests
import os

# 直播源 URL
SOURCE_URL = "https://ghfast.top/https://raw.githubusercontent.com/wangchongzhq/wangchongzhq/2dbe3356a5a073fa4981f54c6b6e53e9117ca10e/109.txt"

# 输出文件
OUTPUT_FILE = "专区/央视频道.txt"

# 创建目录
os.makedirs("专区", exist_ok=True)

# 4K 分组关键字
GROUP_4K = "🇨🇳 4K,#genre#"

def fetch_source():
    resp = requests.get(SOURCE_URL, timeout=10)
    resp.encoding = 'utf-8'
    return resp.text

def extract_4k_group(content):
    """
    提取 🇨🇳 4K 分组及其下所有直播源
    """
    lines = content.splitlines()
    result = []
    include_line = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检查分组行
        if line == GROUP_4K:
            include_line = True
            result.append(line)
            continue

        # 如果在 4K 分组内，追加直播源
        if include_line:
            # 遇到下一个分组行停止抓取
            if (line.startswith("📡") or (",#genre#" in line and line != GROUP_4K)):
                include_line = False
                continue
            result.append(line)

    return result

def save_file(path, lines):
    with open(path, "w", encoding="utf-8-sig") as f:
        for line in lines:
            f.write(line + "\n")
    print(f"✅ 文件已生成: {path}")

def main():
    content = fetch_source()
    group_4k_lines = extract_4k_group(content)

    if not group_4k_lines:
        print("⚠️ 没有抓取到 🇨🇳 4K 分组内容")
    else:
        print(f"总计 {len([l for l in group_4k_lines if l.startswith('http')])} 个 4K 直播源抓取成功。")

    save_file(OUTPUT_FILE, group_4k_lines)

if __name__ == "__main__":
    main()
