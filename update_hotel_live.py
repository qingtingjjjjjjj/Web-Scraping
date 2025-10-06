import requests
import os
import sys

ROOT_DIR = os.getcwd()
SOURCE_URL = "https://raw.githubusercontent.com/wangchongzhq/wangchongzhq/2dbe3356a5a073fa4981f54c6b6e53e9117ca10e/109.txt"

OUTPUT_DIR = os.path.join(ROOT_DIR, "专区")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "4K.txt")
GROUP_KEYWORD = "🇨🇳 4K"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_source():
    try:
        resp = requests.get(SOURCE_URL, timeout=15)
        resp.encoding = 'utf-8'
        print("✅ 源文件抓取成功, 长度:", len(resp.text))
        return resp.text
    except Exception as e:
        print(f"❌ 获取源失败: {e}")
        return ""

def extract_4k_streams(content):
    lines = content.splitlines()
    result = []
    include_line = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if GROUP_KEYWORD in line and ",#genre#" in line:
            include_line = True
            result.append(line)  # 保留分组行
            continue

        if include_line:
            if ",#genre#" in line:  # 遇到下一个分组停止
                break
            if "," in line:  # 保留原始逗号分隔，不改成冒号
                result.append(line)

    print(f"抓取到 {len(result)-1} 个 4K 直播源")  # 减去分组行
    return result

def save_file(path, lines):
    if not lines:
        print("⚠️ 未抓到任何 4K 直播源，文件不会提交")
        print("STREAM_COUNT=0")
        return 0
    with open(path, "w", encoding="utf-8-sig") as f:
        for line in lines:
            f.write(line + "\n")
    print(f"✅ 文件已生成: {os.path.abspath(path)}")
    print(f"STREAM_COUNT={len(lines)-1}")  # 减去分组行
    return len(lines)-1

def main():
    content = fetch_source()
    streams = extract_4k_streams(content) if content else []
    count = save_file(OUTPUT_FILE, streams)
    sys.exit(0 if count > 0 else 1)

if __name__ == "__main__":
    main()
