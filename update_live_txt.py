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

# ===== 接口地址（先提取 AnonymousOrz，再提取 migu_video）=====
sources = {
    "TXT1": "https://hk.gh-proxy.com/https://raw.githubusercontent.com/AnonymousOrz/IPTV/main/Live/collect/央卫内地主流频道cs推流250824(4).txt",
    "TXT2": "https://raw.githubusercontent.com/develop202/migu_video/refs/heads/main/interface.txt"
}

# ===== 频道名清理函数 =====
def simplify_name(name: str) -> str:
    """清理频道名：去掉 HD/高清/cs推流，BRTV，CCTV 特殊处理"""
    # 去掉常见无用标记
    name = re.sub(r'(HD|高清|cs推流)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'BRTV', '', name, flags=re.IGNORECASE)

    name = name.strip()

    # CCTV 频道特殊处理（CCTV01 -> CCTV1）
    cctv_match = re.match(r"CCTV[-_]?0*(\d+)", name, re.IGNORECASE)
    if cctv_match:
        return f"CCTV{int(cctv_match.group(1))}"

    return name

# ===== 抓取并处理数据 =====
def fetch_and_parse(url: str):
    print(f"{BLUE}抓取源:{RESET} {url}")
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        lines = resp.text.strip().splitlines()
        parsed = []

        for line in lines:
            if "," in line:
                name, link = line.split(",", 1)
                name = simplify_name(name)
                parsed.append(f"{name},{link.strip()}")

        print(f"{GREEN}✔ 成功解析 {len(parsed)} 条{RESET}")
        return parsed
    except Exception as e:
        print(f"{RED}✘ 抓取失败: {e}{RESET}")
        return []

# ===== 主函数 =====
def main():
    all_data = []
    for key, url in sources.items():
        data = fetch_and_parse(url)
        all_data.extend(data)

    # 去重：按频道名+链接唯一
    all_data = list(dict.fromkeys(all_data))

    # 写入文件
    if all_data:
        with open(live_file, "w", encoding="utf-8") as f:
            f.write("\n".join(all_data))
        print(f"{YELLOW}已写入 {len(all_data)} 条到 {live_file}{RESET}")
    else:
        print(f"{RED}没有可写入的数据{RESET}")

if __name__ == "__main__":
    main()
