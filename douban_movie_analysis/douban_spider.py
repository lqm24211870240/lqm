import requests
import random
import time
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import pandas as pd

ua = UserAgent()
movie_data_list = []

# 豆瓣TOP250，仅爬前4页共100条
for page_start in range(0, 100, 25):
    headers = {
        "User-Agent": ua.random,
        "Referer": "https://movie.douban.com/",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }
    url = f"https://movie.douban.com/top250?start={page_start}"
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.find_all("li")
        if not items:
            print(f"第{page_start}页未识别到影片列表，跳过")
            time.sleep(random.uniform(3,5))
            continue

        for item in items:
            title_span = item.find("span", class_="title")
            if not title_span:
                continue
            title = title_span.get_text(strip=True)

            info_div = item.find("div", class_="bd")
            info_text = ""
            if info_div and info_div.p:
                info_text = info_div.p.get_text(strip=True).split("\n")[0]
            info_arr = [i.strip() for i in info_text.split("/") if i.strip()]
            year = info_arr[0] if len(info_arr)>=1 else "未知年份"
            area = info_arr[-2] if len(info_arr)>=2 else "未知地区"
            genre = info_arr[-1] if len(info_arr)>=3 else "未知类型"

            # 评分
            score = 0.0
            score_span = item.find("span", class_="rating_num")
            if score_span:
                score = float(score_span.get_text())

            # 【修复】正确抓取评价人数节点：star下倒数第二个span
            people_text = "0人评价"
            star_div = item.find("div", class_="star")
            if star_div:
                span_list = star_div.find_all("span")
                if len(span_list)>=2:
                    people_text = span_list[-2].text

            # 标签
            tag_text = "无标签"
            tag_span = item.find("span", class_="inq")
            if tag_span:
                tag_text = tag_span.get_text(strip=True)

            movie_data_list.append({
                "name": title,
                "year": year,
                "area": area,
                "genre": genre,
                "score": score,
                "comment_people": people_text,
                "tags": tag_text
            })

        sleep_sec = random.uniform(3, 5)
        time.sleep(sleep_sec)
        print(f"已爬取第 {int(page_start/25)+1} 页，当前累计数据：{len(movie_data_list)} 条，休眠{sleep_sec:.1f}s")

    except Exception as err:
        print(f"第{page_start}页爬取出错：{err}")
        time.sleep(random.uniform(4,6))
        continue

df_raw = pd.DataFrame(movie_data_list)
df_raw.to_csv("movie_raw.csv", index=False, encoding="utf-8-sig")
print("======================")
print("爬虫执行结束，数据已写入 movie_raw.csv")
print(f"总有效电影数据：{len(df_raw)} 条")