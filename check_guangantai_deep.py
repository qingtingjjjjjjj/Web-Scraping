#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对 live.txt 中“港澳台,#genre#”分组的直播源做深度测速（更准确）
逻辑：
  - 尝试连接
  - 读取少量数据流（判断能否播放）
  - 统计首包响应时间
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
TIMEOUT = 10
MAX_WORKERS = 8

os.makedirs(OUTPUT_DIR, exist_ok=True)


def parse_live_file(filepath):
    """提取港澳台分组"""
    entries = []
    current_group = None
    with open(filepath, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.endswith("#genre#"):
                current_group = line
                continue
            if current_group == TARGET_GROUP:
                if "," in line:
                    name, url = line.split(",", 1)
                    if url.startswith("http"):
                        entries.append((name.strip(), url.strip()))
    return entries


def deep_test(name, url):
    """深度测速：连接+读取前几KB数据"""
    start = time.time()
    try:
        with requests.get(url, stream=True, timeout=TIMEOUT, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }) as r:
            first_chunk_time = None
            for chunk in r.iter_content(chunk_size=2048):
                if chunk:
                    first_chunk_time = round(time.time() - start, 3)
                    break
            if r.status_code == 200 and first_chunk_time:
                return {
                    "name": name,
                    "url": url,
                    "status": "OK",
                    "time": first_chunk_time
                }
            else:
                return {
                    "name": name,
                    "url": url,
                    "status": f"HTTP {r.status_code}",
                    "time": None
                }
    except Exception as e:
        return {
            "name": name,
            "url": url,
            "status": f"Fail: {e.__class__.__name__}",
            "time": None
        }


def main():
    if not os.path.exists(LIVE_FILE):
        print(f"❌ 未找到 {LIVE_FILE}")
        return

    entries = parse_live_file(LIVE_FILE)
    if not entries:
        print("⚠️ 未找到 '港澳台,#genre#' 分组内容。")
        return

    print(f"发现 {len(entries)} 条港澳台直播源，开始深度测速...\n")

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(deep_test, name, url) for name, url in entries]
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            status = "✅" if res["status"] == "OK" else "❌"
            print(f"{status} {res['name']} - {res['url']}  [{res['status']}]  {res['time']}s")

    # 写入CSV
    with open(RESULT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "url", "status", "time"])
        writer.writeheader()
        writer.writerows(results)

    # 白名单
    ok_list = [r for r in results if r["status"] == "OK"]
    with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
        for r in ok_list:
            f.write(f"{r['name']},{r['url']}\n")

    print(f"\n✅ 测速完成，共 {len(ok_list)} 条可用源。")
    print(f"📁 结果保存在：{OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
