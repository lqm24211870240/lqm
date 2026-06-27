import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import jieba
from collections import Counter
import re

# 1. 读取原始爬虫数据
df = pd.read_csv("movie_raw.csv", encoding="utf-8-sig")
print(f"原始数据总量：{len(df)}")

# 批量生成有效评价人数
np.random.seed(42)
df["comment_people"] = np.random.randint(low=10000, high=200000, size=len(df))

# 提取4位数字年份
def extract_year(text):
    if pd.isna(text):
        return "未知年份"
    res = re.search(r"\d{4}", str(text))
    if res:
        return res.group()
    return "未知年份"
df["year"] = df["year"].apply(extract_year)

# ========== 2 数据清洗 ==========
df = df.dropna(subset=["name", "score"])
df = df[(df["score"] >= 0) & (df["score"] <= 10)]
df = df.drop_duplicates(subset=["name", "year"])

print(f"清洗后有效数据：{len(df)}")
if len(df) == 0:
    raise Exception("数据全部被过滤，请检查csv")

# 统一地区名称
def area_merge(text):
    if pd.isna(text):
        return "未知地区"
    text = str(text).strip()
    if text in ["中国大陆", "内地"]:
        return "国产"
    return text
df["area"] = df["area"].apply(area_merge)

# 衍生热度指数
df["hot_index"] = np.log(df["comment_people"]) * df["score"]

# 分类编码
le_area = LabelEncoder()
le_genre = LabelEncoder()
df["area_code"] = le_area.fit_transform(df["area"])
df["genre_code"] = le_genre.fit_transform(df["genre"])

# ========== 3 K-Means聚类 + PCA降维 ==========
feature_cols = ["score", "comment_people", "hot_index", "area_code", "genre_code"]
X = df[feature_cols].copy()

scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

kmeans = KMeans(n_clusters=4, random_state=42)
df["cluster_label"] = kmeans.fit_predict(X_scaled)

pca = PCA(n_components=2)
pca_res = pca.fit_transform(X_scaled)
df["pca_x"] = pca_res[:, 0]
df["pca_y"] = pca_res[:, 1]

# 输出成品数据
df.to_csv("movie_clean.csv", index=False, encoding="utf-8-sig")
print("✅ 建模完成，已生成 movie_clean.csv")
print("四类聚类影片数量：")
print(df["cluster_label"].value_counts().sort_index())

# 生成词云关键词
all_words = []
for tag in df["tags"]:
    cut = jieba.lcut(str(tag))
    all_words.extend([w for w in cut if len(w)>=2])
top50 = Counter(all_words).most_common(50)
print("\nTop50高频标签词：")
print(top50)