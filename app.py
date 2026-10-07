import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import json

# ضبط إعدادات الصفحة
st.set_page_config(page_title="منصة التعلم الذكية", page_icon="🎓", layout="wide")

# تهيئة جلسة العمل والتخزين (Session State)
if "projects" not in st.session_state:
    st.session_state.projects = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# الشريط الجانبي - إعداد مفتاح API
st.sidebar.title("⚙️ الإعدادات")
api_key = st.sidebar.text_input("أدخل مفتاح Google Gemini API:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.warning("⚠️ يرجى أدخال مفتاح Gemini API في الشريط الجانبي للبدء.")

st.title("🎓 منصة إدارة المشاريع والمحاضرات بالذكاء الاصطناعي")

# إنشاء تبويبات المنصة
tab1, tab2, tab3 = st.tabs(["📚 المحاضرات والمشاريع", "🤖 الشات البوت الذكي", "📝 توليد الأسئلة"])

# ---------------------------------------------------------
# التبويب الأول: رفع وإدارة المحاضرات
# ---------------------------------------------------------
with tab1:
    st.header("إضافة مشروع أو محاضرة جديدة")
    
    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input("اسم المشروع / المحاضرة:")
        project_desc = st.text_area("وصف مختصر:")
    
    with col2:
        uploaded_file = st.file_uploader("ارفع ملف PDF الخاص بالمحاضرة:", type=["pdf"])
        manual_text = st.text_area("أو اكتب/الصق نص المحاضرة هنا:")

    if st.button("حفظ في المنصة 💾"):
        if project_name:
            content = manual_text
            if uploaded_file is not None:
                pdf_reader = PdfReader(uploaded_file)
                pdf_text = ""
                for page in pdf_reader.pages:
                    pdf_text += page.extract_text() or ""
                content += "\n" + pdf_text
            
            st.session_state.projects[project_name] = {
                "description": project_desc,
                "content": content
            }
            st.success(f"تم حفظ '{project_name}' بنجاح!")
        else:
            st.error("يرجى إدخال اسم المشروع/المحاضرة.")

    st.markdown("---")
    st.subheader("📁 المحاضرات والمشاريع المحفوظة")
    if st.session_state.projects:
        selected_proj = st.selectbox("اختر مشروعاً لعرضه:", list(st.session_state.projects.keys()))
        if selected_proj:
            st.write(f"**الوصف:** {st.session_state.projects[selected_proj]['description']}")
            with st.expander("عرض محتوى النص/الـ PDF"):
                st.text_area("المحتوى:", st.session_state.projects[selected_proj]['content'], height=200)
    else:
        st.info("لا توجد مشاريع محفوظة حالياً.")

# ---------------------------------------------------------
# التبويب الثاني: الشات بوت الشارح للمحتوى
# ---------------------------------------------------------
with tab2:
    st.header("💬 اسأل الذكاء الاصطناعي عن المحاضرات")
    
    if st.session_state.projects:
        active_project = st.selectbox("اختر المحاضرة لمناقشتها:", list(st.session_state.projects.keys()), key="chat_proj")
        context = st.session_state.projects[active_project]['content']
        
        # عرض سجل المحادثة
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        user_query = st.chat_input("اسأل أي سؤال حول هذه المحاضرة...")
        if user_query:
            if not api_key:
                st.error("يرجى إدخال API Key أولاً.")
            else:
                st.session_state.chat_history.append({"role": "user", "content": user_query})
                with st.chat_message("user"):
                    st.write(user_query)

                prompt = f"أنت معلم ومساعد دراسي ذكي. استند إلى المحتوى التالي فقط للشرح والإجابة:\n\n{context}\n\nالسؤال: {user_query}"
                
                with st.chat_message("assistant"):
                    response = model.generate_content(prompt)
                    st.write(response.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
    else:
        st.info("يرجى إضافة محاضرة أو مشروع أولاً لاستخدام الشات بوت.")

# ---------------------------------------------------------
# التبويب الثالث: إنشاء الأسئلة والاختبارات
# ---------------------------------------------------------
with tab3:
    st.header("📝 توليد أسئلة واختبارات تلقائية")
    
    if st.session_state.projects:
        quiz_project = st.selectbox("اختر المحاضرة لتوليد أسئلة منها:", list(st.session_state.projects.keys()), key="quiz_proj")
        num_questions = st.slider("عدد الأسئلة المطلوب:", min_value=1, max_value=10, value=3)
        
        if st.button("توليد الأسئلة 🧠"):
            if not api_key:
                st.error("يرجى إدخال API Key أولاً.")
            else:
                content_to_quiz = st.session_state.projects[quiz_project]['content']
                prompt = f"""
                بناءً على المحتوى التالي، قم بإنشاء {num_questions} أسئلة اختيارات من متعدد (MCQ) مع الإجابات النموذجية والشرح باللغة العربية:
                
                المحتوى:
                {content_to_quiz}
                """
                with st.spinner("جاري إعداد الأسئلة..."):
                    quiz_response = model.generate_content(prompt)
                    st.markdown(quiz_response.text)
    else:
        st.info("يرجى إضافة محاضرة أو مشروع أولاً لتوليد الأسئلة.")
