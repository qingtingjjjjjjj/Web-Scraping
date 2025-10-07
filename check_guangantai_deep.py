#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版深度测速：
 - 筛选 live.txt 的 港澳台,#genre# 分组
 - 对每个 URL 做：HEAD -> GET (小量读取) -> 如果是 m3u8 则解析 playlist 并测试第一个 ts 段
 - 重试机制、并发、可选用 ffprobe 进行播放器级探测（如果可用）
 - 输出目录：测速结果/ 港澳台_test_results.csv 和 港澳台_whitelist.txt
"""

import os
import re
import csv
import time
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
import requests
import m3u8

# 配置
LIVE_FILE = "live.txt"
OUTPUT_DIR = "测速结果"
RESULT_CSV = os.path.join(OUTPUT_DIR, "港澳台_test_results.csv")
WHITELIST = os.path.join(OUTPUT_DIR, "港澳台_whitelist.txt")
TARGET_GROUP = "港澳台,#genre#"

MAX_WORKERS = 12
TIMEOUT = (6, 12)         # (connect, read)
RETRIES = 3               # 每个测试最大尝试次数
READ_BYTES = 1024 * 4     # GET 读取首块大小
FFPROBE_TIMEOUT = 12      # ffprobe 最长等待时间（秒）
USE_FFPROBE_IF_AVAILABLE = True

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "VLC/3.0.11 LibVLC/3.0.11"
]

os.makedirs(OUTPUT_DIR, exist_ok=True)


def parse_live_file(filepath):
    """提取 港澳台,#genre# 分组下的 name,url 列表（尽量兼容）"""
    entries = []
    current_group = None
    with open(filepath, encoding="utf-8", errors="ignore") as f:
        lines = [l.rstrip("\n") for l in f]
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.endswith("#genre#") or "港澳台" in line:
            current_group = line
            i += 1
            continue
        if current_group == TARGET_GROUP:
            # 处理 "Name,URL" 或 URL 行
            if "," in line and not line.startswith("#"):
                name, url = line.split(",", 1)
                if url.startswith("http"):
                    entries.append((name.strip(), url.strip()))
            else:
                # 可能上一行是名字，当前是 URL
                if re.match(r'https?://', line):
                    # 回退找上一非空非注释行作为 name
                    name = ""
                    j = i - 1
                    while j >= 0:
                        prev = lines[j].strip()
                        if prev and not prev.startswith("#") and "," not in prev:
                            name = prev
                            break
                        j -= 1
                    entries.append((name, line))
        i += 1

    # 去重
    seen = set()
    cleaned = []
    for n, u in entries:
        if u in seen:
            continue
        seen.add(u)
        cleaned.append((n or u.split("//")[-1].split("/")[0], u))
    return cleaned


def has_ffprobe():
    try:
        subprocess.run(["ffprobe", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception:
        return False


def ffprobe_probe(url, timeout=FFPROBE_TIMEOUT):
    """用 ffprobe 做快速探测（非强制），返回 (ok, note)"""
    cmd = [
        "ffprobe", "-v", "error",
        "-timeout", str(int(timeout * 1e6)),  # ffprobe expects microseconds for -timeout (some builds)
        "-show_streams", "-show_format", "-print_format", "json", url
    ]
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        if p.returncode == 0:
            return True, "ffprobe ok"
        else:
            return False, f"ffprobe rc={p.returncode}"
    except subprocess.TimeoutExpired:
        return False, "ffprobe timeout"
    except Exception as e:
        return False, f"ffprobe error: {e.__class__.__name__}"


def test_single(name, url, session):
    """对单个 URL 做增强检测，返回 dict"""
    result = {
        "name": name,
        "url": url,
        "ok": False,
        "best_time": None,
        "checks": []
    }

    headers_base = {"User-Agent": random.choice(USER_AGENTS)}

    # 多次尝试（重试）
    for attempt in range(1, RETRIES + 1):
        start = time.time()
        try:
            headers = headers_base.copy()
            # 先 HEAD 尝试获取 content-type
            try:
                head = session.head(url, allow_redirects=True, timeout=TIMEOUT, headers=headers)
                ct = head.headers.get("Content-Type", "")
                status = head.status_code
                elapsed_head = round(time.time() - start, 3)
                result["checks"].append(f"HEAD[{attempt}] status={status} ct={ct} t={elapsed_head}s")
                if 200 <= status < 400 and (".m3u8" in url.lower() or "mpegurl" in ct or "vnd.apple.mpegurl" in ct):
                    # 可能是 playlist，继续 GET playlist
                    ok, note, t = check_m3u8_playlist(url, session)
                    if ok:
                        result["ok"] = True
                        result["best_time"] = t
                        result["checks"].append(f"m3u8_ok: {note}")
                        return result
                elif 200 <= status < 400 and head.headers.get("Content-Length"):
                    # 如果有 Content-Length 且 >0，快速判断为可达（但对于某些流这不意味着可播放）
                    cl = int(head.headers.get("Content-Length", "0") or 0)
                    if cl > 0:
                        result["ok"] = True
                        result["best_time"] = elapsed_head
                        result["checks"].append(f"HEAD content-length {cl}")
                        return result
                # 如果 HEAD 没给出足够信息，则用 GET 读取首块
            except requests.RequestException as e_head:
                result["checks"].append(f"HEAD_err[{attempt}]: {e_head.__class__.__name__}")

            # GET 少量数据（stream）
            start_get = time.time()
            resp = session.get(url, stream=True, timeout=TIMEOUT, headers=headers, allow_redirects=True)
            elapsed_get = round(time.time() - start_get, 3)
            status = resp.status_code
            ct = resp.headers.get("Content-Type", "")
            result["checks"].append(f"GET[{attempt}] status={status} ct={ct} t={elapsed_get}s")
            if 200 <= status < 400:
                # 若是 playlist
                if ".m3u8" in url.lower() or "mpegurl" in ct or "vnd.apple.mpegurl" in ct:
                    ok, note, t = check_m3u8_playlist(url, session)
                    if ok:
                        result["ok"] = True
                        result["best_time"] = t
                        result["checks"].append(f"m3u8_ok: {note}")
                        return result
                else:
                    # 读取一小块数据来确认流
                    try:
                        chunk = next(resp.iter_content(chunk_size=READ_BYTES))
                        if chunk and len(chunk) > 0:
                            t = round(time.time() - start_get, 3)
                            result["ok"] = True
                            result["best_time"] = t
                            result["checks"].append(f"GET_data len={len(chunk)} t={t}s")
                            return result
                        else:
                            result["checks"].append(f"GET_no_data[{attempt}]")
                    except Exception as e_iter:
                        result["checks"].append(f"GET_iter_err[{attempt}]: {e_iter.__class__.__name__}")
            else:
                result["checks"].append(f"GET_http_{status}")
        except Exception as e:
            result["checks"].append(f"EXC[{attempt}]: {e.__class__.__name__}")
        # 小间隔后重试
        time.sleep(0.8 * attempt)

    # 最后尝试用 ffprobe（如果可用并且开启）
    if USE_FFPROBE_IF_AVAILABLE and has_ffprobe():
        ok, note = ffprobe_probe(url)
        result["checks"].append(f"ffprobe: {note}")
        if ok:
            result["ok"] = True
            result["best_time"] = None

    return result


def check_m3u8_playlist(url, session):
    """
    下载 m3u8 playlist（master 或 media），解析并测试第一个 ts 段（或第一个 media playlist）。
    返回 (ok:bool, note:str, time:float_or_None)
    """
    try:
        r = session.get(url, timeout=TIMEOUT, headers={"User-Agent": random.choice(USER_AGENTS)})
        if r.status_code != 200:
            return False, f"playlist_http_{r.status_code}", None
        txt = r.text
        m = m3u8.loads(txt)
        # 如果是 master playlist，选择第一个 variant 的 absolute_uri 或基于 url 合成
        if m.is_variant:
            variant = m.playlists[0]
            pl_url = variant.absolute_uri or urljoin(url, variant.uri)
            return check_m3u8_playlist(pl_url, session)
        # media playlist -> 找第一个 segment
        if m.segments and len(m.segments) > 0:
            seg = m.segments[0]
            seg_url = seg.absolute_uri or urljoin(url, seg.uri)
            # 尝试用 GET 请求片段，使用 Range 头只请求前面一小块
            headers = {"User-Agent": random.choice(USER_AGENTS), "Range": "bytes=0-8191"}
            t0 = time.time()
            resp = session.get(seg_url, headers=headers, timeout=TIMEOUT, stream=True, allow_redirects=True)
            t = round(time.time() - t0, 3)
            if resp.status_code in (200, 206):
                # 读取一小块
                try:
                    chunk = next(resp.iter_content(chunk_size=2048))
                    if chunk and len(chunk) > 0:
                        return True, f"segment_ok len={len(chunk)}", t
                    else:
                        return False, "segment_empty", t
                except Exception as e:
                    return False, f"segment_read_err:{e.__class__.__name__}", t
            else:
                return False, f"segment_http_{resp.status_code}", t
        else:
            # playlist 没有 segments，可能是加密或指向 live meta
            return False, "playlist_no_segments", None
    except Exception as e:
        return False, f"playlist_error:{e.__class__.__name__}", None


def main():
    if not os.path.exists(LIVE_FILE):
        print("未找到 live.txt")
        return

    entries = parse_live_file(LIVE_FILE)
    if not entries:
        print("未在 live.txt 中找到目标分组或条目")
        return

    print(f"发现 {len(entries)} 条待测（去重后），开始并发检测 ...")
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_maxsize=MAX_WORKERS)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as exe:
        futures = {exe.submit(test_single, name, url, session): (name, url) for name, url in entries}
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            ok_flag = "✅" if res["ok"] else "❌"
            tshow = f"{res['best_time']}s" if res["best_time"] is not None else "-"
            print(f"{ok_flag} {res['name']} | {tshow} | {res['url']}")
            # 打印简要 checks
            for c in res["checks"][-3:]:
                print(f"   - {c}")

    # 写 CSV
    with open(RESULT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "url", "ok", "best_time", "notes"])
        for r in results:
            notes = " | ".join(r["checks"])
            writer.writerow([r["name"], r["url"], r["ok"], r["best_time"], notes])

    # 写 whitelist（只保留 ok True）
    with open(WHITELIST, "w", encoding="utf-8") as f:
        for r in results:
            if r["ok"]:
                f.write(f"{r['name']},{r['url']}\n")

    print(f"\n完成：结果写入 {OUTPUT_DIR}/")
    ok_count = sum(1 for r in results if r["ok"])
    print(f"可用数量：{ok_count}/{len(results)}")


if __name__ == "__main__":
    main()
