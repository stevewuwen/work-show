CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT,          -- 对应 job_id (str)
    company_name TEXT,       -- 对应 company_name (str)
    source_platform TEXT NOT NULL,    -- 对应 source_platform (str)
    work_type TEXT,                   -- 对应 work_type (str)
    job_url TEXT,                     -- 对应 job_url (str)
    title TEXT NOT NULL,              -- 对应 title (str)
    city TEXT,                        -- 对应 city (list[str]), 存为 JSON 字符串
    category TEXT,                    -- 对应 category (str)
    experience_req TEXT,              -- 对应 experience_req (str)
    education_req TEXT,               -- 对应 education_req (str)
    job_level TEXT,                   -- 对应 job_level (str)
    salary_min REAL,                  -- 对应 salary_min (float)
    salary_max REAL,                  -- 对应 salary_max (float)
    description TEXT,                 -- 对应 description (str)
    description_keywords TEXT,        -- 对应 description_keywords (list[str]), 存为 JSON 字符串
    requirement TEXT,                 -- 对应 requirement (str)
    requirement_keywords TEXT,        -- 对应 requirement_keywords (list[str]), 存为 JSON 字符串
    publish_date INTEGER,             -- 对应 publish_date (int), 时间戳
    crawl_date INTEGER,               -- 对应 crawl_date (int), 时间戳
    extra_info TEXT                   -- 对应 extra_info (dict), 存为 JSON 字符串
);

-- 可选：创建索引以加快常见查询速度（例如按发布时间或城市查询）
CREATE INDEX IF NOT EXISTS idx_jobs_publish_date ON jobs (publish_date);
CREATE INDEX IF NOT EXISTS idx_jobs_city ON jobs (city);