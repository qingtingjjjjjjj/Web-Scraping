import requests
import os

# 直播源 URL
SOURCE_URL = "https://ghfast.top/https://raw.githubusercontent.com/wangchongzhq/wangchongzhq/2dbe3356a5a073fa4981f54c6b6e53e9117ca10e/109.txt"

# 输出文件
OUTPUT_FILE = "专区/央视频道.txt"

# 创建目录
os.makedirs("专区", exist_ok=True)

# 4K 关键字
GROUP_4K = ["4K", "Ultra HD", "UHD"]

def fetch_source():
    resp = requests.get(SOURCE_URL, timeout=10)
    resp.encoding = 'utf-8'
    return resp.text

def extract_4k_lines(content):
    """
    从 TXT 文件中提取包含 4K 的分组行和对应直播源
    """
    lines = content.splitlines()
    result = []
    include_line = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检查分组行
        if line.startswith("📡") and "#genre#" in line:
            include_line = any(k.lower() in line.lower() for k in GROUP_4K)
            if include_line:
                result.append(line)
            continue

        # 直播源行
        if include_line:
            result.append(line)

    return result

def save_file(path, lines):
    with open(path, "w", encoding="utf-8-sig") as f:
        for line in lines:
            f.write(line + "\n")
    print(f"✅ 文件已生成: {path}")

def main():
    content = fetch_source()
    lines_4k = extract_4k_lines(content)

    if not lines_4k:
        print("⚠️ 没有抓取到任何 4K 频道")
    save_file(OUTPUT_FILE, lines_4k)
    print(f"总计 {len([l for l in lines_4k if l.startswith('http')])} 个 4K 直播源写入文件。")

if __name__ == "__main__":
    main()
