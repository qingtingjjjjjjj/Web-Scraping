#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对 live.txt 中“港澳台,#genre#”分组的直播源做深度测速（更准确）
逻辑：
  - 尝试连接并读取少量数据（判断可播放）
  - 首包响应时间测速
  - 若失败自动重试3次
  - 仅当测速结果有变化时，更新 live.txt 中的港澳台分组内容
"""

import os
import re
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

LIVE_FILE = "live.txt"
TARGET_GROUP = "港澳台,#genre#"
TIMEOUT = 10
MAX_WORKERS = 8
RETRY_COUNT = 3


def parse_live_file(filepath):
    """读取所有分组并返回完整文本及港澳台分组内容"""
    with open(filepath, encoding="utf-8", errors="ignore") as f:
        lines = [line.rstrip("\n") for line in f]

    groups = []
    current_group = None
    current_entries = []

    for line in lines:
        if line.endswith("#genre#"):
            if current_group:
                groups.append((current_group, current_entries))
            current_group = line
            current_entries = []
        elif current_group:
            if "," in line:
                current_entries.append(line)
    if current_group:
        groups.append((current_group, current_entries))

    return lines, groups


def deep_test_once(name, url):
    """单次测速"""
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
                return {"name": name, "url": url, "status": "OK", "time": first_chunk_time}
            else:
                return {"name": name, "url": url, "status": f"HTTP {r.status_code}", "time": None}
    except Exception as e:
        return {"name": name, "url": url, "status": f"Fail: {e.__class__.__name__}", "time": None}


def deep_test(name, url):
    """重试测速"""
    for attempt in range(1, RETRY_COUNT + 1):
        result = deep_test_once(name, url)
        if result["status"] == "OK":
            if attempt > 1:
                result["status"] += f" (retry {attempt-1})"
            return result
        else:
            print(f"  ⏳ [{attempt}/{RETRY_COUNT}] {name} 测速失败，重试中...")
            time.sleep(1)
    result["status"] += " (all retries failed)"
    return result


def update_live_file(lines, new_entries):
    """替换港澳台分组内容"""
    updated_lines = []
    inside_target = False
    for line in lines:
        if line == TARGET_GROUP:
            updated_lines.append(line)
            updated_lines.extend(new_entries)
            inside_target = True
            continue
        if inside_target:
            if line.endswith("#genre#"):
                updated_lines.append(line)
                inside_target = False
            # 跳过旧分组内容
            elif not line.strip():
                continue
            else:
                continue
        else:
            updated_lines.append(line)
    return updated_lines


def main():
    if not os.path.exists(LIVE_FILE):
        print(f"❌ 未找到 {LIVE_FILE}")
        return

    lines, groups = parse_live_file(LIVE_FILE)
    entries = []

    for group_name, items in groups:
        if group_name == TARGET_GROUP:
            for line in items:
                name, url = line.split(",", 1)
                if url.startswith("http"):
                    entries.append((name.strip(), url.strip()))

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
            status = "✅" if res["status"].startswith("OK") else "❌"
            print(f"{status} {res['name']} - {res['url']} [{res['status']}] {res['time']}s")

    ok_list = [f"{r['name']},{r['url']}" for r in results if r["status"].startswith("OK")]

    if not ok_list:
        print("❌ 无可用源，不更新。")
        return

    # 检查是否有变化
    old_entries = []
    for g, items in groups:
        if g == TARGET_GROUP:
            old_entries = items
            break

    if set(ok_list) == set(old_entries):
        print("⚙️ 内容无变化，不更新 live.txt。")
        return

    new_lines = update_live_file(lines, ok_list)
    with open(LIVE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")

    print(f"\n✅ 已更新 {LIVE_FILE} 港澳台分组，共 {len(ok_list)} 条可用源。")


if __name__ == "__main__":
    main()
