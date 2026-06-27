import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import jieba
from collections import Counter

# 页面基础设置
st.set_page_config(page_title="豆瓣电影可视化分析系统", layout="wide")
# 缓存加载数据，加速页面
@st.cache_data
def load_data():
    df = pd.read_csv("movie_clean.csv", encoding="utf-8-sig")
    return df
df = load_data()

# 侧边全局筛选器
st.sidebar.title("数据筛选面板")
year_select = st.sidebar.multiselect("选择上映年份", sorted(df["year"].unique()))
area_select = st.sidebar.multiselect("选择制片地区", sorted(df["area"].unique()))
score_min, score_max = st.sidebar.slider("评分区间", 0.0, 10.0, (5.0, 10.0))

# 筛选过滤数据
filter_df = df.copy()
if year_select:
    filter_df = filter_df[filter_df["year"].isin(year_select)]
if area_select:
    filter_df = filter_df[filter_df["area"].isin(area_select)]
filter_df = filter_df[(filter_df["score"] >= score_min) & (filter_df["score"] <= score_max)]

# 侧边导航页面
page = st.sidebar.radio("功能导航", ["数据总览", "类型&地区分析", "评分热度图表", "聚类画像分析", "关键词词云", "原始数据导出"])

# ========== 页面1 数据总览 ==========
if page == "数据总览":
    st.header("🎬 豆瓣电影市场数据总览")
    # 核心指标卡片
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("筛选后影片总数", len(filter_df))
    col2.metric("市场平均评分", round(filter_df["score"].mean(), 2))
    col3.metric("平均评价人数", int(filter_df["comment_people"].mean()))
    col4.metric("最高热度指数", round(filter_df["hot_index"].max(), 2))

    # 年度影片数量折线图
    year_count = filter_df.groupby("year").size().reset_index(name="count")
    fig_year = px.line(year_count, x="year", y="count", title="各年份上映影片数量")
    st.plotly_chart(fig_year, use_container_width=True)

# ========== 页面2 类型&地区分析 ==========
elif page == "类型&地区分析":
    st.header("📊 影片类型、地区分布")
    col_left, col_right = st.columns(2)
    with col_left:
        genre_count = filter_df["genre"].value_counts().reset_index()
        fig_genre = px.bar(genre_count, x="genre", y="count", title="各类型影片数量")
        st.plotly_chart(fig_genre)
    with col_right:
        area_count = filter_df["area"].value_counts().reset_index()
        fig_area = px.pie(area_count, names="area", values="count", title="制片地区占比")
        st.plotly_chart(fig_area)

# ========== 页面3 评分热度图表 ==========
elif page == "评分热度图表":
    st.header("🔥 评分与热度相关性分析")
    # 散点气泡图
    fig_scatter = px.scatter(
        filter_df, x="score", y="comment_people", size="hot_index",
        color="area", hover_data=["name", "genre"],
        title="评分-评价人数散点气泡图（气泡=热度）"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    # 评分箱线图
    fig_box = px.box(filter_df, x="genre", y="score", title="各类型影片评分分布箱线图")
    st.plotly_chart(fig_box, use_container_width=True)

# ========== 页面4 聚类画像分析 ==========
elif page == "聚类画像分析":
    st.header("🤖 K-Means影片聚类（PCA降维可视化）")
    fig_cluster = px.scatter(
        filter_df, x="pca_x", y="pca_y", color="cluster_label",
        hover_data=["name", "score", "genre"],
        title="四类影片聚类散点图（0-3四类市场画像）"
    )
    st.plotly_chart(fig_cluster, use_container_width=True)
    # 聚类分组统计
    st.subheader("各聚类样本统计")
    st.dataframe(filter_df.groupby("cluster_label")[["score", "comment_people", "hot_index"]].mean().round(2))

# ========== 页面5 关键词词云 ==========
elif page == "关键词词云":
    st.header("☁️ 影片标签关键词云")
    # 拼接所有标签分词
    all_words = ""
    for tag in filter_df["tags"]:
        cut = jieba.lcut(tag)
        all_words += " ".join(cut) + " "
    # 移除字体路径避免报错
    wc = WordCloud(width=1000, height=500, background_color="white").generate(all_words)
    plt.figure(figsize=(12,6))
    plt.imshow(wc)
    plt.axis("off")
    st.pyplot(plt)

# ========== 页面6 原始数据导出 ==========
elif page == "原始数据导出":
    st.header("📥 筛选后数据导出")
    st.dataframe(filter_df)
    # 导出csv按钮
    csv_data = filter_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="下载筛选数据CSV",
        data=csv_data,
        file_name="筛选电影数据.csv",
        mime="text/csv"
    )