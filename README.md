**角色设定：**
你是一位精通 Python 数据分析和 Streamlit 开发的专家。请根据以下要求编写一个完整的 `app.py` 脚本。

**1. 数据源说明**
*   **数据库文件**：脚本同级目录下的 `job_info.sqlite`。
*   **表名**：`jobs`。
*   **字段定义（SQL）**：
    ```sql
    CREATE TABLE IF NOT EXISTS jobs (
        job_id TEXT,
        company_name TEXT,
        source_platform TEXT,
        work_type TEXT,
        title TEXT,
        city TEXT,                  -- JSON 数组字符串，例如 '["上海", "北京"]'
        category TEXT,
        experience_req TEXT,
        education_req TEXT,
        salary_min REAL,
        salary_max REAL,
        description_keywords TEXT,  -- JSON 数组字符串
        requirement_keywords TEXT,  -- JSON 数组字符串
        publish_date INTEGER,       -- UNIX 时间戳
        crawl_date INTEGER
    );
    ```

**2. 数据预处理要求 (Pandas)**
*   使用 `sqlite3` 连接并读取数据到 Pandas DataFrame。
*   **JSON 解析**：`city`, `description_keywords`, `requirement_keywords` 字段在数据库中是 JSON 字符串，加载后必须转换为 Python List（若为空或解析失败，设为空列表）。注意，city解析后需要把'市','省'去掉。
*   **时间转换**：将 `publish_date` 从时间戳转换为 datetime 格式。
*   **数据清洗**：剔除 `salary_min` 或 `salary_max` 为空的数据用于薪资分析。
*   **性能优化**：请务必使用 Streamlit 的缓存机制 (`@st.cache_data`) 来加载和预处理数据，避免每次交互都查询数据库。

**3. 界面布局与交互 (Sidebar)**
请在侧边栏 (`st.sidebar`) 设置全局筛选器，筛选后的数据将用于所有图表：
*   **来源平台** (多选)
*   **城市** (多选，注意：因为城市是列表，只要职位包含选定城市之一即可)
*   **工作类型** (work_type， 多选)
*   **工作分类** (category 多选)
*   **学历要求** (多选)
*   **经验要求** (多选)
*   **发布日期范围** (日期选择器)

**4. 可视化需求 (Main Area)**
请使用 **Plotly Express** 库绘制交互式图表，并在页面中使用 `st.tabs` 或 `st.columns` 进行合理布局：

1.  **关键指标卡片 (Metrics)**：显示筛选后的 职位总数、平均薪资、公司数量等。
2.  **职位地理分布 (Top 20 城市)**：
    *   逻辑：因为一个职位可能有多个城市，请先对城市字段进行 `explode` (炸裂) 处理再统计数量。
    *   图表：水平柱状图 (Bar Chart)+地图显示（px.scatter_mapbox）。
3.  **分类分布**：
    *   按 **职位分类 (Category)**、**平台**、**工作类型** 分别绘制 饼图 (Pie/Donut)。
4.  **薪资分布分析**：
    *   绘制 **薪资区间直方图 (Histogram)**（显示平均薪资分布）。
    *   绘制 **不同学历/经验对应的薪资箱线图 (Box Plot)**，展示薪资中位数和离群点。
5.  **发布时间趋势**：
    *   按 **天** 或 **周** 统计职位发布数量，绘制 折线图 (Line Chart)。
6.  **关键词词云 (WordCloud)**：
    *   合并筛选后所有数据的 `description_keywords` 和 `requirement_keywords`。
    *   统计词频并生成词云图（注意：请提供处理中文字体的代码注释或解决方案，以防乱码）。