import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from faker import Faker
import numpy as np

# 初始化数据库
def init_db():
    conn = sqlite3.connect('teaching_app.db')
    c = conn.cursor()
    
    # 创建用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT)''')
    
    # 创建任务进度表
    c.execute('''CREATE TABLE IF NOT EXISTS task_progress
                 (user_id INTEGER,
                  task1 BOOLEAN DEFAULT 0,
                  task2 BOOLEAN DEFAULT 0,
                  task3 BOOLEAN DEFAULT 0,
                  task4 BOOLEAN DEFAULT 0,
                  task5 BOOLEAN DEFAULT 0,
                  FOREIGN KEY(user_id) REFERENCES users(id),
                  PRIMARY KEY(user_id))''')
    
    conn.commit()
    conn.close()

# 密码加密
def make_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 用户认证功能
def register_user(username, password):
    conn = sqlite3.connect('teaching_app.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                 (username, make_hash(password)))
        user_id = c.lastrowid
        # 初始化任务进度
        c.execute("INSERT INTO task_progress (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = sqlite3.connect('teaching_app.db')
    c = conn.cursor()
    c.execute("SELECT id, password FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    if result and result[1] == make_hash(password):
        return result[0]  # 返回用户ID
    return None

# 更新任务进度
def update_task_progress(user_id, task_num):
    conn = sqlite3.connect('teaching_app.db')
    c = conn.cursor()
    c.execute(f"UPDATE task_progress SET task{task_num}=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

# 获取任务进度
def get_task_progress(user_id):
    conn = sqlite3.connect('teaching_app.db')
    c = conn.cursor()
    c.execute("SELECT task1, task2, task3, task4, task5 FROM task_progress WHERE user_id=?", (user_id,))
    progress = c.fetchone()
    conn.close()
    return progress if progress else (0, 0, 0, 0, 0)

# 获取所有用户任务进度
def get_all_progress():
    conn = sqlite3.connect('teaching_app.db')
    c = conn.cursor()
    c.execute('''SELECT users.username, task_progress.* 
                 FROM users JOIN task_progress 
                 ON users.id = task_progress.user_id''')
    results = c.fetchall()
    conn.close()
    return results

# 初始化数据库
init_db()

# 数据加载
@st.cache_data
def load_data():
    fake = Faker('zh_CN')
    np.random.seed(42)
    
    data = {
        '学号': [f'S{10000+i}' for i in range(1000)],
        '姓名': [fake.name() for _ in range(1000)],
        '性别': np.random.choice(['男', '女'], 1000, p=[0.52, 0.48]),
        '年龄': np.random.randint(8, 13, 1000),
        '班级': [f'{np.random.randint(1,5)}年级{np.random.randint(1,10)}班' for _ in range(1000)],
        '语文成绩': np.random.normal(85, 10, 1000).clip(0, 100).astype(int),
        '数学成绩': np.random.normal(90, 8, 1000).clip(0, 100).astype(int),
        '英语成绩': np.random.normal(88, 12, 1000).clip(0, 100).astype(int),
        '出勤率': np.random.uniform(0.85, 1.0, 1000).round(2),
        '注册日期': [fake.date_between(start_date='-2y') for _ in range(1000)]
    }
    
    df = pd.DataFrame(data)
    df[['语文成绩', '数学成绩', '英语成绩']] = df[['语文成绩', '数学成绩', '英语成绩']].astype(int)
    return df

data = load_data()

# 登录/注册界面
def auth_page():
  
    
    # 页面样式
    st.markdown("""
    <style>
        .main {
            background-color: #f5f5f5;
        }
        .stTextInput>div>div>input {
            border-radius: 20px;
            padding: 10px;
        }
        .stButton>button {
            border-radius: 20px;
            background-color: #4CAF50;
            color: white;
            padding: 10px 24px;
            border: none;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 10px 10px 0 0;
            padding: 10px 20px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # 标题和描述
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://via.placeholder.com/150", width=150)
    with col2:
        st.title("教学资源管理系统")
        st.markdown("欢迎使用教学资源平台，请登录或注册")
    
    # 登录注册标签页
    tab1, tab2 = st.tabs(["🔐 登录", "📝 注册"])
    
    with tab1:
        with st.container(border=True):
            st.subheader("用户登录")
            with st.form("登录表单"):
                username = st.text_input("用户名", placeholder="请输入用户名")
                password = st.text_input("密码", type="password", placeholder="请输入密码")
                if st.form_submit_button("登录", use_container_width=True):
                    user_id = login_user(username, password)
                    if user_id:
                        st.session_state.user_id = user_id
                        st.session_state.current_page = "home"
                        st.rerun()
                    else:
                        st.error("用户名或密码错误")
    
    with tab2:
        with st.container(border=True):
            st.subheader("新用户注册")
            with st.form("注册表单"):
                new_username = st.text_input("新用户名", placeholder="设置用户名")
                new_password = st.text_input("新密码", type="password", placeholder="设置密码")
                confirm_password = st.text_input("确认密码", type="password", placeholder="再次输入密码")
                if st.form_submit_button("注册", use_container_width=True):
                    if new_password != confirm_password:
                        st.error("两次输入的密码不一致")
                    elif register_user(new_username, new_password):
                        st.success("注册成功，请登录")
                    else:
                        st.error("用户名已存在")

# 管理员界面
def admin_page():
    # 页面样式
    st.markdown("""
    <style>
        .admin-container {
            border-radius: 10px;
            padding: 20px;
            background-color: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .stats-card {
            border-radius: 10px;
            padding: 15px;
            background-color: #f8f9fa;
            margin-bottom: 15px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.title("🔒 管理员控制台")
        
        # 登录区域
        if not st.session_state.get("is_admin", False):
            with st.form("管理员登录"):
                password = st.text_input("管理员密码", type="password", 
                                       placeholder="输入管理员密码")
                if st.form_submit_button("登录", use_container_width=True):
                    if password == "teacher":
                        st.session_state.is_admin = True
                        st.rerun()
                    else:
                        st.error("密码错误")
            return
        
        # 管理员内容区域
        st.success("✅ 管理员登录成功")
        
        # 获取进度数据
        progress_data = get_all_progress()
        if not progress_data:
            st.warning("没有用户数据")
            return
        
        df = pd.DataFrame(progress_data, 
                        columns=["用户名", "用户ID", "任务1", "任务2", "任务3", "任务4", "任务5"])
        
        # 统计卡片
        st.header("📊 系统概览")
        col1, col2, col3 = st.columns(3)
        with col1:
            with st.container(border=True):
                st.metric("总用户数", len(df))
        with col2:
            with st.container(border=True):
                avg_completion = df[["任务1","任务2","任务3","任务4","任务5"]].mean().mean() * 100
                st.metric("平均完成率", f"{avg_completion:.1f}%")
        with col3:
            with st.container(border=True):
                active_users = len(df[df[["任务1","任务2","任务3","任务4","任务5"]].sum(axis=1) > 0])
                st.metric("活跃用户", active_users)
        
        # 任务完成统计
        st.header("📈 任务完成情况")
        task_stats = df[["任务1","任务2","任务3","任务4","任务5"]].mean() * 100
        st.bar_chart(task_stats)
        
        # 用户详情
        st.header("👥 用户详情")
        with st.expander("查看所有用户数据"):
            st.dataframe(df.style.background_gradient(cmap="Blues"))
        
        # 导出数据
        st.header("💾 数据导出")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="导出CSV",
            data=csv,
            file_name='user_progress.csv',
            mime='text/csv',
            use_container_width=True
        )

# 任务定义
tasks = [
    {
        "id": 1,
        "name": "新手任务",
        "description": "找出所有3年级的学生",
        "condition": lambda df: df[df["班级"].str.contains("3年级")],
        "page": "task1"
    },
    {
        "id": 2, 
        "name": "筛选任务",
        "description": "找出语文成绩大于80分的学生",
        "condition": lambda df: df[df["语文成绩"] > 80],
        "requires": [1],
        "page": "task2"
    },
    {
        "id": 3,
        "name": "组合筛选",
        "description": "找出4年级且数学成绩大于85分的女生",
        "condition": lambda df: df[(df["班级"].str.contains("4年级")) & 
                                (df["数学成绩"] > 85) & 
                                (df["性别"] == "女")],
        "requires": [2],
        "page": "task3"
    },
    {
        "id": 4,
        "name": "精确查找",
        "description": "使用搜索功能找到名字包含'张'的学生",
        "condition": lambda df: df[df["姓名"].str.contains("张")],
        "requires": [3],
        "page": "task4"
    },
    {
        "id": 5,
        "name": "综合挑战",
        "description": "找出5年级英语成绩在70-90分之间的男生",
        "condition": lambda df: df[(df["班级"].str.contains("5年级")) & 
                                (df["英语成绩"] >= 70) & 
                                (df["英语成绩"] <= 90) & 
                                (df["性别"] == "男")],
        "requires": [4],
        "page": "task5"
    }
]

# 初始化状态
if "current_page" not in st.session_state:
    st.session_state.current_page = "auth"
    st.session_state.is_admin = False

# 通用筛选函数
def apply_filters(df, selected_columns):
    filtered_data = df
    
    # 性别筛选
    if "性别" in selected_columns:
        gender = st.radio("选择性别", ["全部", "男", "女"])
        if gender != "全部":
            filtered_data = filtered_data[filtered_data["性别"] == gender]
    
    # 年级筛选
    if "班级" in selected_columns:
        grades = ["全部"] + sorted(filtered_data["班级"].str.extract(r'(\d)年级')[0].unique())
        selected_grade = st.selectbox("选择年级", grades)
        if selected_grade != "全部":
            filtered_data = filtered_data[filtered_data["班级"].str.contains(f"{selected_grade}年级")]
    
    # 班级筛选
    if "班级" in selected_columns:
        classes = ["全部"] + sorted(filtered_data["班级"].unique())
        selected_class = st.selectbox("选择班级", classes)
        if selected_class != "全部":
            filtered_data = filtered_data[filtered_data["班级"] == selected_class]
    
    # 成绩筛选
    if "语文成绩" in selected_columns:
        chinese_range = st.slider(
            "语文成绩范围",
            min_value=int(data["语文成绩"].min()),
            max_value=int(data["语文成绩"].max()),
            value=(60, 100)
        )
        filtered_data = filtered_data[
            (filtered_data["语文成绩"] >= chinese_range[0]) & 
            (filtered_data["语文成绩"] <= chinese_range[1])
        ]
    
    if "数学成绩" in selected_columns:
        math_range = st.slider(
            "数学成绩范围",
            min_value=int(data["数学成绩"].min()),
            max_value=int(data["数学成绩"].max()),
            value=(60, 100)
        )
        filtered_data = filtered_data[
            (filtered_data["数学成绩"] >= math_range[0]) & 
            (filtered_data["数学成绩"] <= math_range[1])
        ]
    
    if "英语成绩" in selected_columns:
        english_range = st.slider(
            "英语成绩范围",
            min_value=int(data["英语成绩"].min()),
            max_value=int(data["英语成绩"].max()),
            value=(60, 100)
        )
        filtered_data = filtered_data[
            (filtered_data["英语成绩"] >= english_range[0]) & 
            (filtered_data["英语成绩"] <= english_range[1])
        ]
    
    return filtered_data[selected_columns]

# 全局导航栏
def show_nav():
    cols = st.columns(len(tasks)+2)  # 增加一个管理员按钮
    with cols[0]:
        if st.button("主页"):
            st.session_state.current_page = "home"
            st.rerun()
    for i, task in enumerate(tasks, 1):
        with cols[i]:
            if st.button(task["name"]):
                st.session_state.current_page = task["page"]
                st.rerun()
    with cols[-1]:
        if st.button("管理员"):
            st.session_state.current_page = "admin"
            st.rerun()

# 主页内容
def show_home():
    show_nav()
    
    # 页面样式
    st.markdown("""
    <style>
        .task-card {
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            background-color: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .task-card.completed {
            border-left: 5px solid #4CAF50;
        }
        .task-card.pending {
            border-left: 5px solid #FF9800;
        }
        .progress-bar {
            height: 10px;
            background-color: #e0e0e0;
            border-radius: 5px;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            border-radius: 5px;
            background-color: #4CAF50;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📊 数据查找闯关挑战")
    st.write(f"👋 欢迎回来, {st.session_state.get('username', '')}")
    
    # 计算完成进度
    progress = get_task_progress(st.session_state.user_id)
    completed = sum(progress)
    total = len(tasks)
    percent = int(completed / total * 100)
    
    # 进度条
    st.subheader(f"总体进度: {completed}/{total} 已完成 ({percent}%)")
    st.markdown(f"""
    <div class="progress-bar">
        <div class="progress-fill" style="width: {percent}%"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # 任务卡片
    st.header("📋 任务列表")
    for i, task in enumerate(tasks, 1):
        is_completed = progress[i-1]
        card_class = "completed" if is_completed else "pending"
        
        with st.container():
            with st.container():
                st.markdown(f"""
                <div class="task-card {card_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3>{'✅' if is_completed else '🔜'} {task['name']}</h3>
                    </div>
                    <p>{task['description']}</p>
                    <small>{'已完成' if is_completed else '待完成'}</small>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"前往{task['name']}", key=f"task_{i}_btn", use_container_width=True):
                    st.session_state.current_page = task["page"]
                    st.rerun()

# 任务页模板
def show_task(task_id):
    show_nav()
    task = next(t for t in tasks if t["id"] == task_id)
    
    # 页面样式
    st.markdown("""
    <style>
        .task-container {
            border-radius: 10px;
            padding: 20px;
            background-color: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .stDataFrame {
            border-radius: 10px;
        }
        .stMultiSelect [data-baseweb=select] {
            min-height: 38px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.title(f"📌 {task['name']}")
        st.markdown(f"**任务描述:** {task['description']}")
        
        # 任务提示和说明
        with st.expander("💡 任务提示"):
            st.write("""
            1. 使用左侧筛选器缩小数据范围
            2. 选择需要显示的列
            3. 确保筛选结果包含所有符合要求的记录
            4. 点击"提交任务"按钮验证结果
            """)
        
        # 数据表格区域
        st.header("📊 数据筛选")
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.subheader("筛选选项")
            selected_columns = st.multiselect(
                "选择显示的列",
                data.columns,
                default=["学号", "姓名", "班级", "语文成绩"]
            )
        
        with col2:
            # 应用所有筛选器
            filtered_data = apply_filters(data, selected_columns)
            
            # 显示数据表格和统计信息
            st.dataframe(filtered_data.style.highlight_max(axis=0))
            
            # 简单统计图表
            if "语文成绩" in selected_columns:
                st.bar_chart(filtered_data["语文成绩"].value_counts())
        
        # 任务提交区域
        st.header("✅ 提交任务")
        if st.button("提交任务", type="primary", use_container_width=True):
            expected = task["condition"](data)
            if set(filtered_data.index).issuperset(set(expected.index)):
                update_task_progress(st.session_state.user_id, task_id)
                
                # 成功反馈
                st.success("""
                ### 🎉 恭喜完成任务！
                你已成功完成本次挑战！
                """)
                st.balloons()
                
                # 显示正确答案
                with st.expander("👀 查看正确答案"):
                    st.dataframe(expected)
                
                # 显示完成徽章
                st.image("https://img.icons8.com/color/96/000000/medal2.png", width=80)
            else:
                # 失败反馈
                st.error("""
                ### ❌ 任务未完成
                你的筛选结果不符合要求，请继续尝试！
                """)
                
                # 提供更多提示
                with st.expander("💡 需要帮助吗？"):
                    st.write(task['description'])
                    st.write("尝试调整筛选条件，确保包含所有符合条件的记录")

# 页面路由
if st.session_state.current_page == "auth":
    auth_page()
elif st.session_state.current_page == "home":
    show_home()
elif st.session_state.current_page == "task1":
    show_task(1)
elif st.session_state.current_page == "task2":
    show_task(2)
elif st.session_state.current_page == "task3":
    show_task(3)
elif st.session_state.current_page == "task4":
    show_task(4)
elif st.session_state.current_page == "task5":
    show_task(5)
elif st.session_state.current_page == "admin":
    admin_page()
