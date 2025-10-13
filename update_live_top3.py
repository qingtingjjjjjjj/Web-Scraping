import os
import re
import asyncio
import aiohttp
from time import time
from datetime import datetime, timedelta
import requests

# ========== 配置 ==========
SOURCE_URL = "https://raw.githubusercontent.com/qingtingjjjjjjj/Web-Scraping/refs/heads/main/live.txt"
OUTPUT_DIR = os.path.join(os.getcwd(), "cmlive")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTFILE = os.path.join(OUTPUT_DIR, "cmlive_top3_per_program.txt")

# ========== 初始化输出 ==========
with open(OUTFILE, "w", encoding="utf-8") as f:
    f.write("")
print(f"📄 输出文件: {OUTFILE}")

# ========== 下载直播源 ==========
print("📡 正在下载直播源...")
try:
    res = requests.get(SOURCE_URL, timeout=60)
    res.encoding = 'utf-8'
    lines = [i.strip() for i in res.text.splitlines() if i.strip()]
    print(f"✅ 成功下载源文件，共 {len(lines)} 行")
except Exception as e:
    print(f"❌ 下载失败: {e}")
    raise SystemExit(1)

# ========== 分组逻辑 ==========
provinces = ["北京","天津","河北","山西","内蒙古","辽宁","吉林","黑龙江","上海","江苏","浙江",
             "安徽","福建","江西","山东","河南","湖北","湖南","广东","广西","海南","重庆","四川",
             "贵州","云南","西藏","陕西","甘肃","青海","宁夏","新疆","港澳台"]

groups = {}
current_group = None

for line in lines:
    if line.endswith(",#genre#"):
        current_group = line.replace(",#genre#", "")
        continue
    if "," not in line:
        continue
    name, link = line.split(",", 1)

    group = None
    if re.search(r"CCTV|CETV", name):
        group = "央视频道"
    elif "卫视" in name:
        group = "卫视频道"
        name = re.match(r"(.*?卫视)", name).group(1)
    else:
        matched = False
        if current_group:
            for prov in provinces:
                if prov in current_group:
                    group = f"{prov}频道"
                    matched = True
                    break
        if not matched:
            for prov in provinces:
                if prov in name:
                    group = f"{prov}频道"
                    matched = True
                    break
        if not matched:
            group = "其他频道"

    groups.setdefault(group, []).append({"name": name, "link": link})

# ========== 异步测速 ==========
async def test_stream(session, item):
    start = time()
    try:
        async with session.get(item["link"], timeout=3) as resp:
            await resp.content.read(512)
        item['time'] = time() - start
    except:
        item['time'] = float("inf")
    return item

async def test_batch(items):
    timeout = aiohttp.ClientTimeout(total=3)
    connector = aiohttp.TCPConnector(limit=800)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        tasks = [test_stream(session, item) for item in items]
        return await asyncio.gather(*tasks)

def test_large_group(items, batch_size=5000):
    all_results = []
    for i in range(0, len(items), batch_size):
        part = items[i:i+batch_size]
        print(f"🚀 分批测速: {i+1}-{i+len(part)} / {len(items)}")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(test_batch(part))
        loop.close()
        all_results.extend(results)
    return all_results

# ========== 测速并保留每个节目最快3条 ==========
print("⏱ 开始异步测速，每个节目保留最快3条源...")
final_groups = {}

for group_name, items in groups.items():
    tested = test_large_group(items)
    # 按节目名称分组
    program_dict = {}
    for item in tested:
        program_dict.setdefault(item['name'], []).append(item)
    # 每个节目保留最快3条
    top_per_program = []
    for prog_name, prog_items in program_dict.items():
        sorted_prog = sorted(prog_items, key=lambda x: x['time'])
        top3 = sorted_prog[:3] if len(sorted_prog) > 3 else sorted_prog
        top_per_program.extend(top3)
    # 按节目内部顺序重新排序（快速优先）
    final_groups[group_name] = sorted(top_per_program, key=lambda x: x['time'])
    print(f"✅ {group_name} 测速完成，每节目保留3条最快源，共 {len(final_groups[group_name])} 条")

# ========== 写入文件 ==========
now = datetime.utcnow() + timedelta(hours=8)
update_time = now.strftime("%Y%m%d %H:%M")

with open(OUTFILE, "w", encoding="utf-8") as f:
    f.write("更新时间,#genre#\n")
    f.write(f"{update_time},https://d.kstore.dev/download/8880/%E5%85%AC%E5%91%8A.mp4\n")
    f.write("关于本源(塔利班维护),https://v.cdnlz12.com/20250131/18183_a5e8965b/index.m3u8\n\n")
    for g, items in final_groups.items():
        f.write(f"{g},#genre#\n")
        for i in items:
            f.write(f"{i['name']},{i['link']}\n")
        f.write("\n")

total = sum(len(v) for v in final_groups.values())
print(f"✅ 完成！已生成 {OUTFILE}，总计 {total} 条（每节目保留3条最快源）")
