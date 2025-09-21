import os
import requests
import re
import base64
import cv2
from datetime import datetime
from bs4 import BeautifulSoup
from translate import Translator
import pytz
from lxml import etree
import asyncio
import time

header = {
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

proxy = {
    'http': '139.9.119.20:80',
    'http': '47.106.144.184:7890',
}

# 验证 tonkiang 可用 IP
def via_tonking(url):
    headers = {
        'Referer': 'http://tonkiang.us/hotellist.html',
        'User-Agent': 'Mozilla/5.0'
    }
    url = f'http://tonkiang.us/alllist.php?s={url}&c=false&y=false'
    try:
        response = requests.get(url, headers=headers, verify=False, proxies=proxy, timeout=10)
        et = etree.HTML(response.text)
        div_text = et.xpath('//div[@class="result"]/div/text()')[1]
        return "暂时失效" not in div_text
    except:
        return False

# 从 tonkiang 获取可用 IP
def get_tonkiang(key_words):
    result_urls = []
    index = 0
    data = {"saerch": f"{key_words}", "Submit": " "}
    url = "http://tonkiang.us/hoteliptv.php"
    resp = requests.post(url, headers=header, data=data, timeout=10, proxies=proxy)
    resp.encoding = 'utf-8'
    et = etree.HTML(resp.text)
    divs = et.xpath('//div[@class="tables"]/div')
    for div in divs:
        try:
            status = div.xpath('./div[3]/div/text()')[0]
            if "暂时失效" not in status:
                if index < 1:
                    url = div.xpath('./div[1]/a/b/text()')[0].strip()
                    if via_tonking(url):
                        result_urls.append(f'http://{url}')
                        index += 1
                else:
                    break
        except:
            continue
    return result_urls

# 生成文件
def gen_files(valid_ips, province, isp, province_en, isp_en):
    index = 0
    udp_filename = f'files/{province}_{isp}.txt'
    with open(udp_filename, 'r', encoding='utf-8') as file:
        data = file.read()
    txt_filename = f'outfiles/{province_en}_{isp_en}.txt'
    with open(txt_filename, 'w', encoding='utf-8') as new_file:
        new_file.write(f'{province}{isp},#genre#\n')
        for url in valid_ips:
            if index < 3:
                new_data = data.replace("udp://", f"{url[0]}/udp/")
                new_file.write(new_data + "\n")
                index += 1
            else:
                continue
    print(f'已生成播放列表，保存至 {txt_filename}')

def filter_files(path, ext):
    return [f for f in os.listdir(path) if f.endswith(ext)]

async def via_url(result_url, mcast):
    valid_ips = []
    video_url = result_url + "/udp/" + mcast
    loop = asyncio.get_running_loop()
    future_obj = loop.run_in_executor(None, cv2.VideoCapture, video_url)
    cap = await future_obj
    if cap.isOpened():
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width > 0 and height > 0 and len(valid_ips) < 3:
            valid_ips.append(result_url)
        cap.release()
    return valid_ips

async def tasks(url_list, mcast):
    tasks = [via_url(url, mcast) for url in url_list]
    ret = await asyncio.gather(*tasks)
    return [e for e in ret if e]

def main():
    files = 'files'
    files_name = [os.path.splitext(f)[0] for f in filter_files(files, ".txt")]
    provinces_isps = sorted([name for name in files_name if name.count('_') == 1])
    print(f"本次查询：{provinces_isps} 的组播节目")

    keywords = []
    for province_isp in provinces_isps:
        try:
            with open(f'files/{province_isp}.txt', 'r', encoding='utf-8') as file:
                lines = [l.strip() for l in file.readlines() if l.strip()]
            if lines:
                first_line = lines[0]
                if "udp://" in first_line:
                    mcast = first_line.split("udp://")[1].split(" ")[0]
                    keywords.append(province_isp + "_" + mcast)
        except FileNotFoundError:
            print(f"文件 '{province_isp}.txt' 不存在. 跳过此文件.")

    for keyword in keywords:
        province, isp, mcast = keyword.split("_")
        translator = Translator(from_lang='chinese', to_lang='english')
        province_en = translator.translate(province).lower()
        org = "Chinanet"
        isp_en = "ctcc" if isp == "电信" else "cucc"
        asn = "4134" if isp == "电信" else "4837"
        others = ''

        timeout_cnt = 0
        result_urls = set()
        while len(result_urls) == 0 and timeout_cnt <= 5:
            try:
                search_url = 'https://fofa.info/result?qbase64='
                search_txt = f'\"udpxy\" && country=\"CN\" && region=\"{province}\" {others} && asn=\"{asn}\"'
                search_txt = base64.b64encode(search_txt.encode('utf-8')).decode('utf-8')
                search_url += search_txt
                print(f"查询运营商 : {province}{isp} ，查询网址 : {search_url}")
                response = requests.get(search_url, headers=header, timeout=30, proxies=proxy)
                response.raise_for_status()
                pattern = r"http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+"
                urls_all = re.findall(pattern, response.text)
                result_urls = set(urls_all)

                valid_ips = asyncio.run(tasks(result_urls, mcast))
                if valid_ips:
                    gen_files(valid_ips, province, isp, province_en, isp_en)
                else:
                    timeout_cnt += 1
                    result_u = get_tonkiang(f'{province}{isp}')
                    if result_u:
                        valid_ips = asyncio.run(tasks(result_u, mcast))
                        if valid_ips:
                            gen_files(valid_ips, province, isp, province_en, isp_en)
            except (requests.Timeout, requests.RequestException):
                timeout_cnt += 1
                if timeout_cnt > 5:
                    print(f"搜索 {province}{isp} 超时次数过多，停止处理")

    # 合并 outfiles txt
    files1 = 'outfiles'
    file_contents = []
    for file_path in filter_files(files1, '.txt'):
        with open(os.path.join(files1, file_path), 'r', encoding="utf-8") as file:
            file_contents.append(file.read())

    with open("IPTV_UDP.txt", "w", encoding="utf-8") as output:
        output.write('\n\n'.join(file_contents))
        local_tz = pytz.timezone("Asia/Shanghai")
        now = datetime.now(local_tz)
        output.write(f"\n更新时间,#genre#\n")
        output.write(f"{now.strftime('%Y-%m-%d')},url\n")
        output.write(f"{now.strftime('%H:%M:%S')},url\n")

    print(f"电视频道成功写入 IPTV_UDP.txt")

if __name__ == "__main__":
    main()
