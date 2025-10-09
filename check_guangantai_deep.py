#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对 live.txt 中“港澳台,#genre#”和“台湾台,#genre#”分组的直播源做深度测速
逻辑：
  - 尝试连接并读取少量数据（判断可播放）
  - 首包响应时间测速
  - 若失败自动重试3次
  - 指定域名免测试
  - 按直播源链接去重（保留第一个出现的条目，格式保持 "节目名称,直播源链接"）
  - 仅当测速结果有变化时，更新 live.txt 中对应分组内容
  - 即使没有可用源，也保留分组标题
"""

import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

LIVE_FILE = "live.txt"
TARGET_GROUPS = ["港澳台,#genre#", "台湾台,#genre#"]
TIMEOUT = 10
MAX_WORKERS = 8
RETRY_COUNT = 3
IMMUNE_DOMAINS = ["bxtv.3a.ink"]


def parse_live_file(filepath):
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
    if any(domain in url for domain in IMMUNE_DOMAINS):
        print(f"💡 {name} 属于免测试域名，直接标记为 OK")
        return {"name": name, "url": url, "status": "OK (免测试)", "time": 0.0}

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


def process_group(group_name, items):
    """处理单个分组"""
    entries = []
    for line in items:
        if "," in line:
            name, url = line.split(",", 1)
            url = url.strip()
            if url.startswith(("http://", "https://")):  # 支持 http 和 https
                entries.append((name.strip(), url, line))  # 保留原行格式
            else:
                print(f"⚠️ 忽略不合法 URL: {line}")

    if not entries:
        print(f"⚠️ 分组 {group_name} 没有可测速源，保留分组标题")
        return group_name, []

    seen_urls = set()
    unique_entries = []
    for name, url, original_line in entries:
        if url not in seen_urls:
            seen_urls.add(url)
            unique_entries.append((name, url, original_line))
        else:
            print(f"🗑️ 去重（保留先出现的）：{name} ({url})")

    print(f"\n🚀 {group_name.replace(',#genre#','')} 去重后 {len(unique_entries)} 条直播源，开始深度测速...\n")

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(deep_test, name, url) for name, url, _ in unique_entries]
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            status = "✅" if res["status"].startswith("OK") else "❌"
            print(f"{status} {res['name']} - {res['url']} [{res['status']}] {res['time']}s")

    ok_list = [f"{r['name']},{r['url']}" for r in results if r["status"].startswith("OK")]
    print(f"✅ {group_name.replace(',#genre#','')} 可用源：{len(ok_list)} 条。\n")
    return group_name, ok_list


def update_live_file(lines, new_entries_dict):
    updated_lines = []
    inside_target = None

    for line in lines:
        if line in TARGET_GROUPS:
            updated_lines.append(line)
            inside_target = line
            updated_lines.extend(new_entries_dict.get(line, []))
            continue

        if inside_target:
            if line.endswith("#genre#") and line not in TARGET_GROUPS:
                updated_lines.append(line)
                inside_target = None
            else:
                continue
        else:
            updated_lines.append(line)

    # 文件末尾可能有新分组，确保它们标题保留
    for group in TARGET_GROUPS:
        if group not in [line for line in updated_lines]:
            updated_lines.append(group)
            updated_lines.extend(new_entries_dict.get(group, []))

    return updated_lines


def main():
    if not os.path.exists(LIVE_FILE):
        print(f"❌ 未找到 {LIVE_FILE}")
        return

    lines, groups = parse_live_file(LIVE_FILE)
    group_dict = dict(groups)

    new_entries_dict = {}
    updated = False

    for group_name in TARGET_GROUPS:
        if group_name in group_dict:
            _, ok_list = process_group(group_name, group_dict[group_name])
            old_list = group_dict[group_name]
            if ok_list != old_list:
                new_entries_dict[group_name] = ok_list
                updated = True
            else:
                new_entries_dict[group_name] = old_list  # 保留空分组标题
                print(f"⚙️ {group_name.replace(',#genre#','')} 内容无变化，不更新。")
        else:
            new_entries_dict[group_name] = []
            print(f"⚠️ 未找到分组：{group_name}")

    if not updated:
        print("🟢 所有分组内容均无变化，不更新 live.txt。")
        return

    new_lines = update_live_file(lines, new_entries_dict)
    with open(LIVE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")

    print(f"\n✅ 已更新 {LIVE_FILE}，共更新 {len(new_entries_dict)} 个分组。")


if __name__ == "__main__":
    main()
