import streamlit as st
from utils.ai_processor import get_problem_help, grade_solution
from utils.zhupai_student import question_service
from utils.db_operations import get_user_data2, get_know_com
from utils.coze_ppt_generate import get_coze_response
from utils.coze_task_guide import get_coze_response as get_coze_response_task_guide
import json
import streamlit.components.v1 as components
import os
import requests
from utils.coze_file import CozeChatAPI  # 新增导入
from upload_file import generate_coze_data  # 新增导入
import contextlib
import traceback
import base64
import io
from utils.coze_test_generate import get_coze_response as get_coze_response3
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
def save_uploaded_file(uploaded_file):
    """保存上传的文件到指定目录"""
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path
def coze_upload_file(file_path):
    """调用Coze文件上传API"""
    url = "https://api.coze.cn/v1/files/upload"
    headers = {
        "Authorization": "Bearer pat_YIYDDe70PzCmnZrK30PhZI2HND1xBanYMc2hdhEFDyQvskVvHTc4mIxPv3h06H3P"########################################################
    }

    try:
        with open(file_path, 'rb') as f:
            file_type = 'application/octet-stream'
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                file_type = 'image/jpeg'
            elif file_path.lower().endswith('.pdf'):
                file_type = 'application/pdf'

            files = {'file': (os.path.basename(file_path), f, file_type)}
            response = requests.post(url, headers=headers, files=files)
            response.raise_for_status()
            return response
    except Exception as e:
        raise RuntimeError(f"文件上传失败: {str(e)}")

def show():
    
    if 'user_email' not in st.session_state or not st.session_state.user_email:
        st.warning("请先登录！")
        return

    if st.session_state.user_type == 0:
        if "student_test_ai" not in st.session_state:
            st.session_state.student_test_ai=[]
        with st.sidebar:
            st.sidebar.info("🌈 伴学灵宝-云端AI课件")
            st.sidebar.page_link("app.py", label="🏠 首页")
            st.sidebar.page_link("pages/1_课程讲义学习_课程知识搜集.py", label="📚 课程讲义学习")
            st.sidebar.page_link("pages/2_讲义知识学伴_AI教学设计.py", label="🎓 讲义知识理解")
            st.sidebar.page_link("pages/3_讲义练习辅导_课堂游戏资源.py", label="🎮 讲义练习辅导")
            st.sidebar.page_link("pages/4_课堂任务完成_发布课堂任务.py", label="✨ 课堂任务完成")
            st.sidebar.page_link("pages/5_自行选择训练_试卷批改.py", label="✏️ 自行选择训练")
            st.sidebar.page_link("pages/6_个人学情查询_班级数据管理.py", label="📈 个人学情查询")
        st.markdown("""
<div style="background: linear-gradient(135deg, #e1f5fe 0%, #b3e5fc 100%); 
            padding: 1.5rem; border-radius: 12px; margin-top: 1rem;
            box-shadow: 0 6px 16px rgba(3,169,244,0.2);
            border-left: 5px solid #03a9f4;
            transition: transform 0.3s ease;">
    <h3 style="color: #0277bd; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);">🗣️ AI练习辅导</h3>
    <p style="font-size: 0.95rem; color: #01579b;">📝 这个工具将展示来自课程讲义的题目,你可以在此进行题目练习,随后使用AI进行批阅</p>
</div>
""", unsafe_allow_html=True)         
        # 获取练习题（假设已存在 session 中）
        try:
            exercise_keys = [k for k in st.session_state.keys() if k.startswith("exercise_")]
        except:
            exercise_keys = []
        if exercise_keys:
            st.subheader("📘 当前练习题")
            
            # 初始化闯关进度
            if 'completed_exercises' not in st.session_state:
                st.session_state.completed_exercises = set()
            
            # 显示进度条
            progress = len(st.session_state.completed_exercises) / len(exercise_keys)
            st.progress(progress, text=f"闯关进度: {int(progress*100)}% ({len(st.session_state.completed_exercises)}/{len(exercise_keys)})")

            for i, key in enumerate(sorted(exercise_keys), start=1):
                        question = st.session_state[key]
                        st.write(f"题目{i}：{question}")
                        code_key = f"student_test_ai_xcode_{i}"
                        run_key = f"student_test_ai_xrun_{i}"
                        output_key = f"student_test_ai_xoutput_{i}"
                        por_key = f"student_test_ai_xpor_{i}" 
                        default_code = "# 🧿在这里编写你的代码"

                        # 代码输入框
                        code = st.text_area(" ", value=default_code, height=200, key=code_key)

                        if f"student_test_ai_xpor_{i}" not in st.session_state:
                            st.session_state[f"student_test_ai_xpor_{i}"] = " "  # Default code

                        por = st.text_area("🧿在此处与AI进行交流", value=st.session_state[f"student_test_ai_xpor_{i}"], height=100, key=por_key)

                        # Update session state when the user modifies the code
                        if por != st.session_state[f"student_test_ai_xpor_{i}"]:
                            st.session_state[f"student_test_ai_xpor_{i}"] = por
                            ##############################

                        col1, col2, col3, col4 = st.columns(4)

                        # 运行代码按钮
                        if col1.button("▶ 运行代码", key=run_key):
                            st.subheader("💡 输出结果：")
                            try:
                                with contextlib.redirect_stdout(io.StringIO()) as f:
                                    with contextlib.redirect_stderr(f):
                                        exec(code, {})
                                output = f.getvalue()
                                st.session_state[output_key] = output
                                st.code(output)
                            except Exception:
                                st.session_state[output_key] = traceback.format_exc()
                                st.error("❌ 运行出错：")
                                st.code(st.session_state[output_key])

                        # 显示之前的输出
                        elif output_key in st.session_state:
                            st.subheader("💡 运行结果：")
                            st.code(st.session_state[output_key])
                        # AI 辅导按钮
                        if col2.button(f"🧠AI辅导--题目 {i}"):
                            st.session_state.completed_exercises.add(key)
                            solution = st.session_state[code_key]
                            data = {
                                "题目": question,
                                "学生代码": solution,
                                "指令":por
                            }
                            # with st.spinner("⏳ 正在获取指导，请稍候..."):
                            #     guide = get_coze_response_task_guide(str(data))
                            #     for answer in guide['answers']:
                            #             combined_answers = "\n\n".join([f"• {a}" for a in guide['answers']])

                            #     with st.expander("🧠 AI 辅导建议（点击展开）"):
                            #         st.info(combined_answers)
                                 
                            with st.spinner("⏳ 正在获取指导，请稍候..."):
                                guide = get_coze_response_task_guide(str(data))
                                combined_answers = "\n\n".join([f"• {a}" for a in guide['answers']])
                            with st.expander("🧠 AI 辅导建议（点击展开）"):
                                st.markdown(
                                    f"<div style='font-size: 14px; line-height: 1.6;'>{combined_answers.replace(chr(10), '<br>')}</div>",
                                    unsafe_allow_html=True
                                )
                        

        st.divider()

        
        # knowledge_p  = st.text_input("请输入您想要练习的题目类型(例如:for循环,递归...)", key="knowledge_generate")     
        # test_submit=st.button("题目生成",key="knowledge_generate_button")
        # if test_submit:
        #         with st.spinner("⏳ AI 正在生成题目，请稍候..."):
        #             print("knowledge",knowledge_p)
        #             test=get_coze_response3(knowledge_p)
        #             print(test)
        #             parsed_response = json.loads(test['answers'][0])
        #                             # 一次性生成题目列表并赋值给 session_state.student_test_ai
        #             st.session_state.student_test_ai = [list(item.values())[0] for item in parsed_response['output']]
        # if st.session_state.student_test_ai:
        #         # 展示结果
        #             st.write("✅ 当前题目列表（student_test_ai）：")
        #             for i, q in enumerate(st.session_state.student_test_ai, start=1):
        #                 st.write(f"题目{i}：{q}")
        #                 code_key = f"student_test_ai_code_{i}"
        #                 run_key = f"student_test_ai_run_{i}"
        #                 output_key = f"student_test_ai_output_{i}"
        #                 default_code = "# 在这里编写你的代码"

        #                 # 代码输入框
        #                 code = st.text_area(" ", value=default_code, height=200, key=code_key)

        #                 col1, col2, col3, col4 = st.columns(4)

        #                 # 运行代码按钮
        #                 if col1.button("▶ 运行代码", key=run_key):
        #                     st.subheader("💡 输出结果：")
        #                     try:
        #                         with contextlib.redirect_stdout(io.StringIO()) as f:
        #                             with contextlib.redirect_stderr(f):
        #                                 exec(code, {})
        #                         output = f.getvalue()
        #                         st.session_state[output_key] = output
        #                         st.code(output)
        #                     except Exception:
        #                         st.session_state[output_key] = traceback.format_exc()
        #                         st.error("❌ 运行出错：")
        #                         st.code(st.session_state[output_key])

        #                 # 显示之前的输出
        #                 elif output_key in st.session_state:
        #                     st.subheader("💡 运行结果：")
        #                     st.code(st.session_state[output_key])
        #                 # AI 辅导按钮
        #                 if col2.button(f"🧠AI辅导--题目 {i}"):
        #                     solution = st.session_state[code_key]
        #                     data = {
        #                         "题目": q,
        #                         "学生代码": solution
        #                     }
        #                     with st.spinner("⏳ 正在获取指导，请稍候..."):
        #                         guide = get_coze_response_task_guide(str(data))
        #                         for answer in guide['answers']:
        #                                 combined_answers = "\n\n".join([f"• {a}" for a in guide['answers']])

        #                         with st.expander("🧠 AI 辅导建议（点击展开）"):
        #                             st.info(combined_answers)

    if st.session_state.user_type == 1:
            st.sidebar.info("🌈 伴学灵宝-云端AI课件")            
            st.sidebar.page_link("app.py", label="🏠 首页")
            st.sidebar.page_link("pages/1_课程讲义学习_课程知识搜集.py", label="📚 课程知识搜集")
            st.sidebar.page_link("pages/2_讲义知识学伴_AI教学设计.py", label="🎓 AI教学设计")
            st.sidebar.page_link("pages/3_讲义练习辅导_课堂游戏资源.py", label="🎮 课堂游戏资源")
            st.sidebar.page_link("pages/4_课堂任务完成_发布课堂任务.py", label="✨ 发布课堂任务")
            st.sidebar.page_link("pages/5_自行选择训练_试卷批改.py", label="✏️ 试卷批改")
            st.sidebar.page_link("pages/6_个人学情查询_班级数据管理.py", label="📈 班级数据管理")          
            st.markdown("""
<div style="background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%); 
            padding: 1.5rem; border-radius: 12px; margin-top: 1rem;
            box-shadow: 0 6px 16px rgba(156,39,176,0.2);
            border-left: 5px solid #9c27b0;
            transition: transform 0.3s ease;">
    <h3 style="color: #7b1fa2; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);">🎲 点名游戏生成器</h3>
    <p style="font-size: 0.95rem; color: #4a148c;">🎯 这个工具允许您通过上传班级名单文件（如：Excel、CSV等），
            系统将自动生成一个点名游戏，您可以在课堂上使用这个游戏提高学生参与度。</p>
</div>
""", unsafe_allow_html=True)
            uploaded_file = st.file_uploader("选择文件", type=["txt", "csv", "pdf", "docx", "jpg", "png","pptx","xlsx"])
            user_text = "."
            submitted = st.button("📤 提交班级名单表",key="game_click") 
            if submitted:
                    if uploaded_file and user_text:
                        try:
                            # 第一阶段：文件保存和上传
                            saved_path = save_uploaded_file(uploaded_file)
                            st.success(f"文件保存成功：{saved_path}")

                            with st.spinner("正在上传文件到Coze..."):
                                response = coze_upload_file(saved_path)

                            # 生成output.json
                            data = response.json()
                            b = data['data']['id']
                            output_data = {"file_id": b, "user_text": user_text}
                            with open("output.json", "w") as f:
                                json.dump(output_data, f)

                            # 第二阶段：生成请求数据并调用API
                            with st.spinner("生成请求参数..."):
                                request_data = generate_coze_data()
                                if not request_data:
                                    raise ValueError("生成请求参数失败")

                            # 初始化API客户端
                            coze_api = CozeChatAPI(
                                api_key="pat_yPgDslmEycjg3h67cLVr9cVj8bxi01tQ5BCjfedRMmNqppkkl1ULqGXhGQYDP5bu",
                                bot_id="7489751691873943552"
                            )

                            # 第三阶段：调用聊天API并显示结果
                            with st.spinner("正在获取AI响应..."):
                                api_result = coze_api.ask_question(request_data)  
                                html_content = json.loads(api_result['answers'][0])
                                html_content=html_content.get("code")
                                components.html(html_content, height=700)
                        except Exception as e:
                            st.error(f"发生错误：{e}")

            st.markdown("""
<div style="background: linear-gradient(135deg, #a7c5eb 0%, #7b61a3 100%); 
            padding: 1.5rem; border-radius: 12px; margin-top: 1rem;
            box-shadow: 0 6px 16px rgba(123, 97, 163, 0.2);
            border-left: 5px solid #5e35b1;
            transition: transform 0.3s ease;">
    <h3 style="color: #512da8; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);">🗺️ 教学资源生成</h3>
    <p style="font-size: 0.95rem; color: #311b92;">🏙️ 这个工具允许您通过输入python知识点,AI将结合知识库中的python教材,以及优秀的ppt设计文案,给给您生成ppt文件</p>
</div>
""", unsafe_allow_html=True)
            if  f"pptx_" not in st.session_state:
                st.session_state.pptx_ = "bit"
            user_input = st.text_input("请输入讲义内容：",key=st.session_state.pptx_)
            if st.button("提交",key="pptx"):
                print(user_input)
                with st.spinner("思考中..."):
                    response = get_coze_response(str(user_input))
                    try:
                        parsed_response = json.loads(response['answers'][0])
                        st.session_state.ppt = parsed_response.get("ppt", " ")
                        print(st.session_state.ppt )
                        # 提取所有缩略图链接
                        st.session_state.thumbnails = [
                            pic["thumbnail"] for pic in parsed_response.get("pic", [])
                        ]
                        print(st.session_state.thumbnails)
                    except (KeyError, IndexError, json.JSONDecodeError) as e:
                        print(f"解析出错: {e}")
                        st.session_state.ppt = " "
                        st.session_state.thumbnails = []
                    if "ppt" in st.session_state and st.session_state.ppt.strip():
                        st.markdown(f"📥 [点击下载 PPT]( {st.session_state.ppt} )", unsafe_allow_html=True)

                    # 展示 PPT 缩略图（可折叠）
                    if "thumbnails" in st.session_state and st.session_state.thumbnails:
                        with st.expander("📂 展示 PPT 预览缩略图"):
                            for index, thumbnail in enumerate(st.session_state.thumbnails):
                                st.image(thumbnail, caption=f"第 {index + 1} 页")    
                    # 重新渲染以显示最新消息         
if __name__ == "__main__":
        show()
