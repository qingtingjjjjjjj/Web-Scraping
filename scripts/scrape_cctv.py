#!/usr/bin/env python3
# coding: utf-8
"""
scripts/scrape_cctv.py
爬取央视卫视频道直播源，检测可用性，输出 single file: output/cctv.txt
格式：前半部分为 "频道名|url" 列表，后半部分为 M3U 播放列表（以 ===M3U START=== 分隔）
"""
import argparse
import os
import re
import sys
import time
from typing import List, Tuple, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm

# ------- 配置区 -------
CHANNELS = [
    ("CCTV-4 中文国际", "https://tv.cctv.com/lm/cctv4/"),
    ("CCTV-2 财经", "https://tv.cctv.com/lm/cctv2/"),
    ("CCTV-3 综艺", "https://tv.cctv.com/lm/cctv3/"),
    ("CCTV-5 体育", "https://tv.cctv.com/lm/cctv5/"),
    ("CCTV-6 电影", "https://tv.cctv.com/lm/cctv6/"),
    ("CCTV-8 电视剧", "https://tv.cctv.com/lm/cctv8/"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

URL_RE = re.compile(
    r'(https?://[^\s"\']+\.(?:m3u8|mp4|flv|ts|aac|m4s)(?:[^\s"\']*)|https?://[^\s"\']+?/playlist\.m3u8[^\s"\']*)',
    flags=re.IGNORECASE
)
IFRAME_RE = re.compile(r'<iframe[^>]+src=["\']([^"\']+)["\']', re.I)
VIDEO_SRC_RE = re.compile(r'<video[^>]+src=["\']([^"\']+)["\']', re.I)

# ------- 工具函数 -------
def safe_get(url: str, timeout: int = 8, max_retries: int = 2) -> Optional[requests.Response]:
    for i in range(max_retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
            return r
        except Exception:
            if i >= max_retries:
                return None
            time.sleep(1)
    return None

def head_or_range_check(url: str, timeout: int = 8) -> bool:
    try:
        r = requests.head(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return True
    except Exception:
        pass
    try:
        r2 = requests.get(url, headers={**HEADERS, "Range": "bytes=0-1024"}, timeout=timeout, stream=True, allow_redirects=True)
        if r2.status_code in (200, 206):
            return True
    except Exception:
        return False
    return False

def extract_candidate_urls_from_text(text: str, base_url: Optional[str] = None) -> List[str]:
    found = set()
    for m in URL_RE.findall(text):
        found.add(m if m.startswith("http") else (urljoin(base_url, m) if base_url else m))
    for match in IFRAME_RE.findall(text):
        found.add(match if match.startswith("http") else (urljoin(base_url, match) if base_url else match))
    for match in VIDEO_SRC_RE.findall(text):
        found.add(match if match.startswith("http") else (urljoin(base_url, match) if base_url else match))
    for m in re.findall(r'(["\'])(//[^"\']+?\.(?:m3u8|mp4|flv|ts|m4s)[^"\']*)\1', text, flags=re.I):
        url0 = m[1]
        if url0.startswith("//"):
            found.add("https:" + url0)
        else:
            found.add(url0)
    for m in re.findall(r'(["\'])(/[^"\']+?\.(?:m3u8|mp4|flv|ts|m4s)[^"\']*)\1', text, flags=re.I):
        if base_url:
            found.add(urljoin(base_url, m[1]))
    return list(found)

def normalize_url(u: str) -> str:
    return u.strip().replace('\\/', '/')

def scrape_channel(entry: Tuple[str, str], timeout: int = 8) -> List[Tuple[str, str]]:
    name, target = entry
    candidates = []
    if target.startswith("http://") or target.startswith("https://"):
        page_url = target
        r = safe_get(page_url, timeout=timeout, max_retries=2)
        if not r:
            return []
        text = r.text
        base = page_url
        cand = extract_candidate_urls_from_text(text, base_url=base)
        for iframe_url in cand[:]:
            if "m3u8" in iframe_url.lower() or iframe_url.lower().endswith((".mp4", ".flv")):
                continue
            if re.match(r'^https?://', iframe_url):
                rr = safe_get(iframe_url, timeout=timeout, max_retries=1)
                if rr:
                    cand += extract_candidate_urls_from_text(rr.text, base_url=iframe_url)
        candidates = [normalize_url(u) for u in set(cand)]
    else:
        guess_urls = [
            f"https://tv.cctv.com/lm/{target}/",
            f"https://tv.cctv.com/live/{target}.shtml",
            f"https://tv.cctv.com/{target}/",
        ]
        cand = []
        for gu in guess_urls:
            r = safe_get(gu, timeout=timeout, max_retries=1)
            if not r:
                continue
            cand += extract_candidate_urls_from_text(r.text, base_url=gu)
        candidates = [normalize_url(u) for u in set(cand)]

    playable = []
    candidates_sorted = sorted(candidates, key=lambda x: (0 if ".m3u8" in x.lower() else 1, -len(x)))
    for url in candidates_sorted:
        if not url.lower().startswith("http"):
            continue
        ok = head_or_range_check(url, timeout=timeout)
        if ok:
            playable.append((name, url))
            if ".m3u8" in url.lower():
                break
    return playable

def main(output_dir: str = "output", timeout: int = 8):
    results = []
    print("开始爬取 CCTV 直播源 ...")
    for entry in tqdm(CHANNELS, desc="channels"):
        try:
            found = scrape_channel(entry, timeout=timeout)
            if found:
                results.append(found[0])
                print(f"[OK] {found[0][0]} -> {found[0][1]}")
            else:
                print(f"[NO] 未找到可用地址: {entry[0]} ({entry[1]})")
        except Exception as e:
            print(f"[ERR] {entry[0]} error: {e}")

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "cctv.txt")

    # 写入 single cctv.txt：先写简单列表，再写分隔和标准 M3U
    with open(output_file, "w", encoding="utf-8") as f:
        # 简单列表部分（每行：频道名|url）
        for name, url in results:
            f.write(f"{name}|{url}\n")

        # 分隔与 M3U 部分
        f.write("\n===M3U START===\n")
        f.write("#EXTM3U\n")
        for name, url in results:
            f.write(f'#EXTINF:-1,{name}\n')
            f.write(f"{url}\n")

    print(f"输出完成: {output_file}")
    print("Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape CCTV live streams and generate single cctv.txt")
    parser.add_argument("--output-dir", default="output", help="输出目录（默认 output）")
    parser.add_argument("--timeout", type=int, default=8, help="网络超时时间（秒）")
    args = parser.parse_args()
    main(output_dir=args.output_dir, timeout=args.timeout)
