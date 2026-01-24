"""
职位数据分析仪表板
基于 Streamlit + Plotly + WordCloud 构建
"""

import sqlite3
import json
from collections import Counter

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="职位数据分析仪表板",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 职位数据分析仪表板")
st.markdown("---")

# ============================================================
# 中国主要城市经纬度映射（用于地图可视化）
# ============================================================
CITY_COORDINATES = {
    "北京": (39.9042, 116.4074),
    "上海": (31.2304, 121.4737),
    "广州": (23.1291, 113.2644),
    "深圳": (22.5431, 114.0579),
    "成都": (30.5728, 104.0668),
    "武汉": (30.5928, 114.3055),
    "西安": (34.3416, 108.9398),
    "杭州": (30.2741, 120.1551),
    "重庆": (29.5630, 106.5516),
    "南京": (32.0603, 118.7969),
    "天津": (39.3434, 117.3616),
    "苏州": (31.2990, 120.5853),
    "郑州": (34.7466, 113.6254),
    "长沙": (28.2282, 112.9388),
    "东莞": (23.0430, 113.7633),
    "沈阳": (41.8057, 123.4315),
    "青岛": (36.0671, 120.3826),
    "合肥": (31.8206, 117.2272),
    "佛山": (23.0218, 113.1219),
    "宁波": (29.8683, 121.5440),
    "昆明": (25.0389, 102.7183),
    "大连": (38.9140, 121.6147),
    "福州": (26.0745, 119.2965),
    "厦门": (24.4798, 118.0894),
    "哈尔滨": (45.8038, 126.5350),
    "济南": (36.6512, 117.1201),
    "温州": (28.0006, 120.6721),
    "南宁": (22.8170, 108.3665),
    "长春": (43.8171, 125.3235),
    "泉州": (24.8741, 118.6757),
    "石家庄": (38.0428, 114.5149),
    "贵阳": (26.6470, 106.6302),
    "南昌": (28.6820, 115.8579),
    "金华": (29.0792, 119.6474),
    "常州": (31.8106, 119.9740),
    "惠州": (23.1116, 114.4158),
    "嘉兴": (30.7522, 120.7550),
    "太原": (37.8706, 112.5489),
    "徐州": (34.2044, 117.2860),
    "南通": (31.9807, 120.8940),
    "珠海": (22.2710, 113.5767),
    "中山": (22.5176, 113.3926),
    "保定": (38.8739, 115.4646),
    "兰州": (36.0611, 103.8343),
    "台州": (28.6563, 121.4205),
    "绍兴": (30.0306, 120.5800),
    "烟台": (37.4638, 121.4479),
    "廊坊": (39.5186, 116.6831),
    "洛阳": (34.6197, 112.4540),
    "乌鲁木齐": (43.8256, 87.6168),
    "无锡": (31.4912, 120.3119),
    "海口": (20.0440, 110.1999),
    "三亚": (18.2528, 109.5119),
    "拉萨": (29.6500, 91.1000),
    "银川": (38.4872, 106.2309),
    "西宁": (36.6171, 101.7782),
    "呼和浩特": (40.8424, 111.7490),
    "香港": (22.3193, 114.1694),
    "澳门": (22.1987, 113.5439),
    "台北": (25.0330, 121.5654),
}


# ============================================================
# 数据加载与预处理（带缓存）
# ============================================================
@st.cache_data
def load_data():
    """
    从 SQLite 数据库加载数据并进行预处理
    使用 @st.cache_data 缓存，避免重复查询数据库
    """
    # 连接数据库
    conn = sqlite3.connect("job_info.sqlite")
    df = pd.read_sql_query("SELECT * FROM jobs", conn)
    conn.close()

    # JSON 解析辅助函数
    def parse_json_list(value):
        """安全解析 JSON 数组字符串"""
        if pd.isna(value) or value == "" or value is None:
            return []
        try:
            result = json.loads(value)
            if isinstance(result, list):
                return result
            return []
        except (json.JSONDecodeError, TypeError):
            return []

    def clean_city_name(city):
        """清理城市名称，去除'市'、'省'后缀"""
        if isinstance(city, str):
            return city.replace("市", "").replace("省", "")
        return city

    # 解析 JSON 字段
    df["city"] = df["city"].apply(parse_json_list)
    df["city"] = df["city"].apply(lambda cities: [clean_city_name(c) for c in cities])
    df["description_keywords"] = df["description_keywords"].apply(parse_json_list)
    df["requirement_keywords"] = df["requirement_keywords"].apply(parse_json_list)

    # 时间转换
    df["publish_date"] = pd.to_datetime(df["publish_date"], unit="s", errors="coerce")
    df["crawl_date"] = pd.to_datetime(df["crawl_date"], unit="s", errors="coerce")

    # 计算平均薪资（用于有薪资数据的记录）
    df["salary_avg"] = df.apply(
        lambda row: (row["salary_min"] + row["salary_max"]) / 2
        if pd.notna(row["salary_min"]) and pd.notna(row["salary_max"])
        else np.nan,
        axis=1,
    )

    return df


# 加载数据
df = load_data()

# ============================================================
# 侧边栏筛选器
# ============================================================
st.sidebar.header("🔍 数据筛选")

# 来源平台筛选
all_platforms = df["source_platform"].dropna().unique().tolist()
selected_platforms = st.sidebar.multiselect(
    "来源平台", options=all_platforms, default=[]
)

# 城市筛选（需要展开列表）
all_cities = sorted(set(city for cities in df["city"] for city in cities if city))
selected_cities = st.sidebar.multiselect("城市", options=all_cities, default=[])

# 工作类型筛选
all_work_types = df["work_type"].dropna().unique().tolist()
selected_work_types = st.sidebar.multiselect(
    "工作类型", options=all_work_types, default=[]
)

# 工作分类筛选
all_categories = df["category"].dropna().unique().tolist()
selected_categories = st.sidebar.multiselect(
    "工作分类", options=all_categories, default=[]
)

# 学历要求筛选
all_education = df["education_req"].dropna().unique().tolist()
selected_education = st.sidebar.multiselect(
    "学历要求", options=all_education, default=[]
)

# 经验要求筛选
all_experience = df["experience_req"].dropna().unique().tolist()
selected_experience = st.sidebar.multiselect(
    "经验要求", options=all_experience, default=[]
)

# 发布日期范围
min_date = df["publish_date"].min()
max_date = df["publish_date"].max()

if pd.notna(min_date) and pd.notna(max_date):
    date_range = st.sidebar.date_input(
        "发布日期范围",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date(),
    )
else:
    date_range = None


# ============================================================
# 数据筛选逻辑
# ============================================================
def filter_data(
    df, platforms, cities, work_types, categories, education, experience, date_range
):
    """根据筛选条件过滤数据"""
    filtered = df.copy()

    # 来源平台
    if platforms:
        filtered = filtered[filtered["source_platform"].isin(platforms)]

    # 城市（只要职位包含选定城市之一即可）
    if cities:
        filtered = filtered[
            filtered["city"].apply(lambda x: any(c in cities for c in x))
        ]

    # 工作类型
    if work_types:
        filtered = filtered[filtered["work_type"].isin(work_types)]

    # 工作分类
    if categories:
        filtered = filtered[filtered["category"].isin(categories)]

    # 学历要求
    if education:
        filtered = filtered[filtered["education_req"].isin(education)]

    # 经验要求
    if experience:
        filtered = filtered[filtered["experience_req"].isin(experience)]

    # 发布日期范围
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        filtered = filtered[
            (filtered["publish_date"].dt.date >= start_date)
            & (filtered["publish_date"].dt.date <= end_date)
        ]

    return filtered


# 应用筛选
filtered_df = filter_data(
    df,
    selected_platforms,
    selected_cities,
    selected_work_types,
    selected_categories,
    selected_education,
    selected_experience,
    date_range,
)

# 薪资分析数据（剔除空值）
salary_df = filtered_df.dropna(subset=["salary_min", "salary_max"])

# ============================================================
# 1. 关键指标卡片
# ============================================================
st.subheader("📈 关键指标")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("职位总数", f"{len(filtered_df):,}")

with col2:
    avg_salary = salary_df["salary_avg"].mean() if len(salary_df) > 0 else 0
    st.metric("平均薪资", f"¥{avg_salary:,.0f}")

with col3:
    company_count = filtered_df["company_name"].nunique()
    st.metric("公司数量", f"{company_count:,}")

with col4:
    median_salary = salary_df["salary_avg"].median() if len(salary_df) > 0 else 0
    st.metric("薪资中位数", f"¥{median_salary:,.0f}")

with col5:
    max_salary = salary_df["salary_max"].max() if len(salary_df) > 0 else 0
    st.metric("最高薪资", f"¥{max_salary:,.0f}")

st.markdown("---")

# ============================================================
# 使用 Tabs 进行布局
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "🗺️ 地理分布",
        "📊 分类分布",
        "💰 薪资分析",
        "📅 时间趋势",
        "☁️ 关键词词云",
        "📋 原始数据",
    ]
)

# ============================================================
# Tab 1: 职位地理分布
# ============================================================
with tab1:
    st.subheader("🗺️ 职位地理分布 (Top 20 城市)")

    # 炸裂城市字段统计
    city_exploded = filtered_df.explode("city")
    city_counts = city_exploded["city"].value_counts().head(20).reset_index()
    city_counts.columns = ["city", "count"]

    col1, col2 = st.columns(2)

    with col1:
        # 水平柱状图
        fig_bar = px.bar(
            city_counts.sort_values("count", ascending=True),
            x="count",
            y="city",
            orientation="h",
            title="Top 20 城市职位数量",
            labels={"count": "职位数量", "city": "城市"},
            color="count",
            color_continuous_scale="Blues",
        )
        fig_bar.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        # 地图可视化
        # 添加经纬度
        city_counts["lat"] = city_counts["city"].apply(
            lambda x: CITY_COORDINATES.get(x, (None, None))[0]
        )
        city_counts["lon"] = city_counts["city"].apply(
            lambda x: CITY_COORDINATES.get(x, (None, None))[1]
        )

        # 过滤掉没有坐标的城市
        city_map_df = city_counts.dropna(subset=["lat", "lon"])

        if len(city_map_df) > 0:
            fig_map = px.scatter_mapbox(
                city_map_df,
                lat="lat",
                lon="lon",
                size="count",
                color="count",
                hover_name="city",
                hover_data={"count": True, "lat": False, "lon": False},
                title="职位地理分布地图",
                color_continuous_scale="Viridis",
                size_max=50,
                zoom=3,
            )
            fig_map.update_layout(
                mapbox_style="open-street-map",
                height=600,
                margin={"r": 0, "t": 40, "l": 0, "b": 0},
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("没有可用的城市坐标数据用于地图显示")

# ============================================================
# Tab 2: 分类分布
# ============================================================
with tab2:
    st.subheader("📊 分类分布")

    col1, col2, col3 = st.columns(3)

    with col1:
        # 职位分类饼图
        category_counts = filtered_df["category"].value_counts().reset_index()
        category_counts.columns = ["category", "count"]

        fig_category = px.pie(
            category_counts.head(10),
            values="count",
            names="category",
            title="职位分类分布 (Top 10)",
            hole=0.4,
        )
        fig_category.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_category, use_container_width=True)

    with col2:
        # 平台分布饼图
        platform_counts = filtered_df["source_platform"].value_counts().reset_index()
        platform_counts.columns = ["platform", "count"]

        fig_platform = px.pie(
            platform_counts,
            values="count",
            names="platform",
            title="来源平台分布",
            hole=0.4,
        )
        fig_platform.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_platform, use_container_width=True)

    with col3:
        # 工作类型分布饼图
        work_type_counts = filtered_df["work_type"].value_counts().reset_index()
        work_type_counts.columns = ["work_type", "count"]

        fig_work_type = px.pie(
            work_type_counts,
            values="count",
            names="work_type",
            title="工作类型分布",
            hole=0.4,
        )
        fig_work_type.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_work_type, use_container_width=True)

# ============================================================
# Tab 3: 薪资分析
# ============================================================
with tab3:
    st.subheader("💰 薪资分布分析")

    if len(salary_df) > 0:
        col1, col2 = st.columns(2)

        with col1:
            # 薪资区间直方图
            fig_hist = px.histogram(
                salary_df,
                x="salary_avg",
                nbins=30,
                title="平均薪资分布直方图",
                labels={"salary_avg": "平均薪资 (元)", "count": "职位数量"},
                color_discrete_sequence=["#636EFA"],
            )
            fig_hist.update_layout(
                xaxis_title="平均薪资 (元)", yaxis_title="职位数量", bargap=0.1
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        with col2:
            # 学历对应薪资箱线图
            fig_edu_box = px.box(
                salary_df,
                x="education_req",
                y="salary_avg",
                title="不同学历要求的薪资分布",
                labels={"education_req": "学历要求", "salary_avg": "平均薪资 (元)"},
                color="education_req",
            )
            fig_edu_box.update_layout(showlegend=False)
            st.plotly_chart(fig_edu_box, use_container_width=True)

        # 经验对应薪资箱线图
        fig_exp_box = px.box(
            salary_df,
            x="experience_req",
            y="salary_avg",
            title="不同经验要求的薪资分布",
            labels={"experience_req": "经验要求", "salary_avg": "平均薪资 (元)"},
            color="experience_req",
        )
        fig_exp_box.update_layout(showlegend=False)
        st.plotly_chart(fig_exp_box, use_container_width=True)

        # 薪资统计表格
        st.markdown("#### 📊 薪资统计摘要")
        salary_stats = (
            salary_df.groupby("education_req")["salary_avg"]
            .agg(["count", "mean", "median", "min", "max"])
            .round(0)
        )
        salary_stats.columns = ["职位数", "平均值", "中位数", "最小值", "最大值"]
        st.dataframe(salary_stats, use_container_width=True)
    else:
        st.warning("筛选后无有效薪资数据")

# ============================================================
# Tab 4: 发布时间趋势
# ============================================================
with tab4:
    st.subheader("📅 发布时间趋势")

    # 时间粒度选择
    time_granularity = st.radio("选择时间粒度", ["按天", "按周"], horizontal=True)

    time_df = filtered_df.dropna(subset=["publish_date"]).copy()

    if len(time_df) > 0:
        if time_granularity == "按天":
            time_df["date"] = time_df["publish_date"].dt.date
            time_counts = time_df.groupby("date").size().reset_index(name="count")
            time_counts["date"] = pd.to_datetime(time_counts["date"])
        else:
            time_df["week"] = (
                time_df["publish_date"].dt.to_period("W").apply(lambda x: x.start_time)
            )
            time_counts = time_df.groupby("week").size().reset_index(name="count")
            time_counts.columns = ["date", "count"]

        fig_line = px.line(
            time_counts,
            x="date",
            y="count",
            title=f"职位发布趋势（{time_granularity}）",
            labels={"date": "日期", "count": "职位数量"},
            markers=True,
        )
        fig_line.update_layout(
            xaxis_title="日期", yaxis_title="职位数量", hovermode="x unified"
        )
        st.plotly_chart(fig_line, use_container_width=True)

        # 显示数据表格
        with st.expander("查看详细数据"):
            st.dataframe(time_counts, use_container_width=True)
    else:
        st.warning("筛选后无有效时间数据")

# ============================================================
# Tab 5: 关键词词云
# ============================================================
with tab5:
    st.subheader("☁️ 关键词词云")

    # 合并所有关键词
    all_desc_keywords = []
    all_req_keywords = []

    for keywords in filtered_df["description_keywords"]:
        if isinstance(keywords, list):
            all_desc_keywords.extend(keywords)

    for keywords in filtered_df["requirement_keywords"]:
        if isinstance(keywords, list):
            all_req_keywords.extend(keywords)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 职位描述关键词")
        if all_desc_keywords:
            desc_freq = Counter(all_desc_keywords)

            # 生成词云
            # 中文字体设置说明：
            # 1. 如果系统安装了中文字体，可以指定字体路径，例如：
            #    font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"  # Linux
            #    font_path = "C:/Windows/Fonts/msyh.ttc"  # Windows (微软雅黑)
            #    font_path = "/System/Library/Fonts/PingFang.ttc"  # macOS
            # 2. 如果不指定字体，中文可能显示为方块
            # 3. 推荐在部署时确保系统有中文字体支持

            try:
                # 尝试使用系统字体（根据操作系统选择）
                import platform

                system = platform.system()
                if system == "Windows":
                    font_path = "C:/Windows/Fonts/msyh.ttc"
                elif system == "Darwin":  # macOS
                    font_path = "/System/Library/Fonts/PingFang.ttc"
                else:  # Linux
                    font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"

                wc_desc = WordCloud(
                    width=800,
                    height=400,
                    background_color="white",
                    font_path=font_path,
                    max_words=100,
                    colormap="viridis",
                ).generate_from_frequencies(desc_freq)
            except Exception:
                # 如果字体加载失败，使用默认设置
                wc_desc = WordCloud(
                    width=800,
                    height=400,
                    background_color="white",
                    max_words=100,
                    colormap="viridis",
                ).generate_from_frequencies(desc_freq)

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wc_desc, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)

            # 显示词频统计
            with st.expander("查看关键词词频 (Top 20)"):
                top_desc = pd.DataFrame(
                    desc_freq.most_common(20), columns=["关键词", "频次"]
                )
                st.dataframe(top_desc, use_container_width=True)
        else:
            st.info("暂无职位描述关键词数据")

    with col2:
        st.markdown("#### 职位要求关键词")
        if all_req_keywords:
            req_freq = Counter(all_req_keywords)

            try:
                import platform

                system = platform.system()
                if system == "Windows":
                    font_path = "C:/Windows/Fonts/msyh.ttc"
                elif system == "Darwin":
                    font_path = "/System/Library/Fonts/PingFang.ttc"
                else:
                    font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"

                wc_req = WordCloud(
                    width=800,
                    height=400,
                    background_color="white",
                    font_path=font_path,
                    max_words=100,
                    colormap="plasma",
                ).generate_from_frequencies(req_freq)
            except Exception:
                wc_req = WordCloud(
                    width=800,
                    height=400,
                    background_color="white",
                    max_words=100,
                    colormap="plasma",
                ).generate_from_frequencies(req_freq)

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wc_req, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)

            with st.expander("查看关键词词频 (Top 20)"):
                top_req = pd.DataFrame(
                    req_freq.most_common(20), columns=["关键词", "频次"]
                )
                st.dataframe(top_req, use_container_width=True)
        else:
            st.info("暂无职位要求关键词数据")

# ============================================================
# Tab 6: 原始数据
# ============================================================
with tab6:
    st.subheader("📋 原始数据查看")

    st.write(f"共 {len(filtered_df)} 条记录")

    # 显示数据（隐藏复杂的列表字段）
    display_cols = [
        "job_id",
        "company_name",
        "title",
        "source_platform",
        "work_type",
        "category",
        "education_req",
        "experience_req",
        "salary_min",
        "salary_max",
        "publish_date",
    ]

    st.dataframe(
        filtered_df[display_cols].head(100), use_container_width=True, height=600
    )

    st.caption("* 仅显示前 100 条记录")

# ============================================================
# 页脚
# ============================================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        📊 职位数据分析仪表板 | 基于 Streamlit + Plotly 构建
    </div>
    """,
    unsafe_allow_html=True,
)
