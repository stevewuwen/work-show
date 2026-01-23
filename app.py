import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dataclasses import asdict
from datetime import datetime
import random
import uuid
from work_show.core.models import Item


# --- 2. 模拟数据生成 (用于演示，实际使用时请替换为你的数据库读取逻辑) ---
def load_data() -> pd.DataFrame:
    # 这里模拟生成 100 条数据
    categories = ["算法类", "工程类", "产品类", "运营类", "设计类"]
    cities = [["北京"], ["上海"], ["深圳"], ["杭州"], ["北京", "上海"], ["远程"]]
    educations = ["本科", "硕士", "博士", "大专"]
    experiences = ["1-3年", "3-5年", "5-10年", "应届生"]

    data = []
    for _ in range(200):
        salary_base = random.randint(10, 50)
        item = Item(
            job_id=str(uuid.uuid4()),
            company_name=random.choice(
                ["字节跳动", "腾讯", "美团", "初创公司A", "国企B"]
            ),
            source_platform=random.choice(["Boss直聘", "官网", "拉勾"]),
            work_type=random.choice(["社招", "校招", "实习"]),
            title=f"高级{random.choice(categories)}工程师",
            city=random.choice(cities),
            category=random.choice(categories),
            education_req=random.choice(educations),
            experience_req=random.choice(experiences),
            salary_min=salary_base * 1000,
            salary_max=(salary_base + random.randint(5, 20)) * 1000,
            description_keywords=random.sample(
                ["Python", "Java", "Go", "SQL", "AI", "Kubernetes"], k=3
            ),
            publish_date=int(datetime.now().timestamp())
            - random.randint(0, 86400 * 30),
        )
        data.append(item)

    # 将 Dataclass 列表转换为 DataFrame
    df = pd.DataFrame([asdict(i) for i in data])

    # 数据清洗与转换
    # 1. 处理时间戳
    df["publish_date"] = pd.to_datetime(df["publish_date"], unit="s")
    # 2. 计算平均薪资 (用于分析)
    df["salary_avg"] = (df["salary_min"] + df["salary_max"]) / 2
    return df


# --- 3. Streamlit 页面逻辑 ---
def main():
    st.set_page_config(page_title="招聘数据分析看板", layout="wide", page_icon="📊")

    st.title("📊 招聘数据可视化分析")
    st.markdown("---")

    # 加载数据
    with st.spinner("正在加载数据..."):
        df_raw = load_data()

    # --- 侧边栏：全局过滤器 ---
    st.sidebar.header("🔍 筛选条件")

    # 城市筛选 (处理 list 类型的城市)
    all_cities = sorted(
        list(set([c for sublist in df_raw["city"] if sublist for c in sublist]))
    )
    selected_cities = st.sidebar.multiselect(
        "选择城市", all_cities, default=all_cities[:2]
    )

    # 岗位分类筛选
    selected_categories = st.sidebar.multiselect(
        "岗位分类", df_raw["category"].unique(), default=df_raw["category"].unique()
    )

    # 学历筛选
    selected_edu = st.sidebar.multiselect(
        "学历要求",
        df_raw["education_req"].unique(),
        default=df_raw["education_req"].unique(),
    )

    # --- 数据过滤逻辑 ---
    # 城市过滤逻辑比较特殊，因为是 list
    mask_city = df_raw["city"].apply(
        lambda x: any(item in selected_cities for item in x) if x else False
    )
    mask_category = df_raw["category"].isin(selected_categories)
    mask_edu = df_raw["education_req"].isin(selected_edu)

    df = df_raw[mask_city & mask_category & mask_edu]

    if df.empty:
        st.warning("当前筛选条件下没有数据。")
        return

    # --- 顶部 KPI 指标 ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("职位总数", len(df))
    with col2:
        avg_salary = df["salary_avg"].mean()
        st.metric("平均薪资 (月)", f"¥{avg_salary:,.0f}")
    with col3:
        st.metric("覆盖公司数", df["company_name"].nunique())
    with col4:
        st.metric("主要来源", df["source_platform"].mode()[0])

    st.markdown("---")

    # --- Tab 分页展示 ---
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📈 概览分布", "💰 薪资分析", "🗺️ 地域分析", "📋 数据详情"]
    )

    # Tab 1: 概览分布
    with tab1:
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("岗位分类分布")
            fig_cat = px.pie(df, names="category", title="岗位类别占比", hole=0.4)
            st.plotly_chart(fig_cat, use_container_width=True)

        with col_right:
            st.subheader("学历与经验要求")
            # 这是一个热力图式的统计
            df_heatmap = (
                df.groupby(["education_req", "experience_req"])
                .size()
                .reset_index(name="count")
            )
            fig_heat = px.bar(
                df_heatmap,
                x="education_req",
                y="count",
                color="experience_req",
                title="学历 vs 经验要求分布",
                barmode="group",
            )
            st.plotly_chart(fig_heat, use_container_width=True)

        st.subheader("公司招聘数量 Top 10")
        top_companies = df["company_name"].value_counts().head(10).reset_index()
        top_companies.columns = ["company", "count"]
        fig_company = px.bar(
            top_companies, x="count", y="company", orientation="h", title="热门招聘公司"
        )
        st.plotly_chart(fig_company, use_container_width=True)

    # Tab 2: 薪资分析
    with tab2:
        st.info("注：薪资单位为人民币/月，取薪资范围的平均值计算。")

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.subheader("学历与薪资关系")
            fig_box_edu = px.box(
                df,
                x="education_req",
                y="salary_avg",
                color="education_req",
                title="不同学历的薪资分布",
            )
            st.plotly_chart(fig_box_edu, use_container_width=True)

        with col_s2:
            st.subheader("经验与薪资关系")
            # 指定顺序
            order_exp = ["应届生", "1-3年", "3-5年", "5-10年"]
            # 过滤出存在的数据用于排序
            current_order = [x for x in order_exp if x in df["experience_req"].unique()]

            fig_box_exp = px.box(
                df,
                x="experience_req",
                y="salary_avg",
                color="experience_req",
                category_orders={"experience_req": current_order},
                title="不同经验要求的薪资分布",
            )
            st.plotly_chart(fig_box_exp, use_container_width=True)

        st.subheader("岗位类别平均薪资排行")
        avg_salary_by_cat = (
            df.groupby("category")["salary_avg"]
            .mean()
            .sort_values(ascending=False)
            .reset_index()
        )
        fig_bar_salary = px.bar(
            avg_salary_by_cat,
            x="category",
            y="salary_avg",
            color="salary_avg",
            labels={"salary_avg": "平均薪资"},
            title="各分类平均薪资",
        )
        st.plotly_chart(fig_bar_salary, use_container_width=True)

    # Tab 3: 地域与关键词分析
    with tab3:
        col_c1, col_c2 = st.columns([1, 1])

        with col_c1:
            st.subheader("城市职位数量")
            # 需要将 city list 炸开 (Explode)
            df_exploded = df.explode("city")
            city_counts = df_exploded["city"].value_counts().reset_index()
            city_counts.columns = ["city", "count"]
            fig_city = px.bar(city_counts, x="city", y="count", title="各城市职位数量")
            st.plotly_chart(fig_city, use_container_width=True)

        with col_c2:
            st.subheader("热门技能关键词 (Top 15)")
            # 统计 Keywords
            all_keywords = []
            # 过滤 None 值
            keywords_series = df["description_keywords"].dropna()
            for k_list in keywords_series:
                all_keywords.extend(k_list)

            if all_keywords:
                kw_df = pd.Series(all_keywords).value_counts().head(15).reset_index()
                kw_df.columns = ["keyword", "count"]
                fig_kw = px.bar(
                    kw_df,
                    x="count",
                    y="keyword",
                    orientation="h",
                    title="描述关键词频率",
                    color="count",
                )
                st.plotly_chart(fig_kw, use_container_width=True)
            else:
                st.write("暂无关键词数据")

    # Tab 4: 原始数据
    with tab4:
        st.subheader("原始数据概览")
        # 简单格式化一下显示
        display_cols = [
            "title",
            "company_name",
            "city",
            "salary_min",
            "salary_max",
            "education_req",
            "category",
        ]
        st.dataframe(df[display_cols], use_container_width=True)

        st.download_button(
            label="下载当前筛选结果 (CSV)",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="filtered_jobs.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
