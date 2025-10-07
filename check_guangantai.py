#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对 live.txt 中“港澳台,#genre#”分组的直播源测速（响应时间）。
输出：
  - 测速结果/港澳台_test_results.csv
  - 测速结果/港澳台_whitelist.txt
"""

import os
import re
import csv
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

LIVE_FILE = "live.txt"
OUTPUT_DIR = "测速结果"
WHITELIST_FILE = os.path.join(OUTPUT_DIR, "港澳台_whitelist.txt")
RESULT_FILE = os.path.join(OUTPUT_DIR, "港澳台_test_results.csv")

TARGET_GROUP = "港澳台,#genre#"
TIMEOUT = 8
MAX_WORKERS = 10

os.makedirs(OUTPUT_DIR, exist_ok=True)


def parse_live_file(filepath):
    """提取 港澳台,#genre# 分组下的频道与URL"""
    entries = []
    current_group = None
    with open(filepath, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # 检测分组
            if line.endswith("#genre#"):
                current_group = line
                continue
            # 港澳台分组下的内容
            if current_group == TARGET_GROUP:
                if "," in line:
                    name, url = line.split(",", 1)
                    if url.startswith("http"):
                        entries.append((name.strip(), url.strip()))
    return entries


def test_url(name, url):
    """测速函数：返回响应时间（秒）"""
    start = time.time()
    try:
        resp = requests.get(url, stream=True, timeout=TIMEOUT)
        elapsed = round(time.time() - start, 3)
        if resp.status_code == 200:
            return {"name": name, "url": url, "status": "OK", "time": elapsed}
        else:
            return {"name": name, "url": url, "status": f"HTTP {resp.status_code}", "time": elapsed}
    except Exception as e:
        return {"name": name, "url": url, "status": f"Fail: {e.__class__.__name__}", "time": None}


def main():
    if not os.path.exists(LIVE_FILE):
        print(f"❌ 未找到 {LIVE_FILE}")
        return

    entries = parse_live_file(LIVE_FILE)
    if not entries:
        print("⚠️ 未找到 '港澳台,#genre#' 分组内容。")
        return

    print(f"发现 {len(entries)} 条直播源，开始测速...")

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(test_url, name, url) for name, url in entries]
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            status = "✅" if res["status"] == "OK" else "❌"
            print(f"{status} {res['name']} - {res['url']}  [{res['status']}]  {res['time']}s")

    # 写入 CSV
    with open(RESULT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "url", "status", "time"])
        writer.writeheader()
        writer.writerows(results)

    # 写入白名单
    ok_list = [r for r in results if r["status"] == "OK"]
    with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
        for r in ok_list:
            f.write(f"{r['name']},{r['url']}\n")

    print(f"\n✅ 测速完成，共 {len(ok_list)} 条可用源。")
    print(f"📁 结果文件保存在：{OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
