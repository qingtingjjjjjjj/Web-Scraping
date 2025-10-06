import requests
import os

# 根目录路径（即脚本所在目录）
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

# 直播源 URL
SOURCE_URL = "https://raw.githubusercontent.com/wangchongzhq/wangchongzhq/2dbe3356a5a073fa4981f54c6b6e53e9117ca10e/109.txt"

# 输出目录和文件
OUTPUT_DIR = os.path.join(ROOT_DIR, "专区")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "4K.txt")

GROUP_KEYWORD = "🇨🇳 4K"

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 获取源文件
def fetch_source():
    try:
        resp = requests.get(SOURCE_URL, timeout=15)
        resp.encoding = 'utf-8'
        return resp.text
    except Exception as e:
        print(f"❌ 获取源失败: {e}")
        return ""

# 提取 4K 分组下的直播源（不包含分组行）
def extract_4k_streams(content):
    lines = content.splitlines()
    result = []
    include_line = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 找到 4K 分组行
        if GROUP_KEYWORD in line and ",#genre#" in line:
            include_line = True
            continue

        # 分组内抓取直播源
        if include_line:
            if ",#genre#" in line:  # 遇到下一个分组停止
                break
            parts = line.split(",", 1)
            if len(parts) == 2:
                result.append(f"{parts[0]}: {parts[1]}")  # 只保留直播源，不输出分组

    return result

# 保存到文件
def save_file(path, lines):
    if not lines:
        print("⚠️ 没有抓取到直播源，文件未生成")
        return
    with open(path, "w", encoding="utf-8-sig") as f:
        for line in lines:
            f.write(line + "\n")
    print(f"✅ 文件已生成: {os.path.abspath(path)}")

# 主函数
def main():
    content = fetch_source()
    if not content:
        print("❌ 源文件为空")
        return

    streams = extract_4k_streams(content)
    print(f"抓取到 {len(streams)} 个 4K 直播源")

    save_file(OUTPUT_FILE, streams)

if __name__ == "__main__":
    main()
