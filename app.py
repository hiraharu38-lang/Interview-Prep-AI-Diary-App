import streamlit as st
from google import genai
import time

st.set_page_config(
    page_title="一問一答！面接採点AI",
    page_icon="🎯",
    layout="centered"
)

SELECT_MODEL = 'gemini-3.1-flash-lite'

# APIの初期化
api_key = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=api_key)

# 状態管理の初期化
if "step" not in st.session_state:
    st.session_state.step = "input_diary"
if "diary_theme" not in st.session_state:
    st.session_state.diary_theme = ""
if "ai_question" not in st.session_state:
    st.session_state.ai_question = ""
if "user_answer" not in st.session_state:
    st.session_state.user_answer = ""
if "score_result" not in st.session_state:
    st.session_state.score_result = ""

# 🔥 10回全滅するまでは絶対にエラーを漏らさない関数
def generate_with_retry(prompt):
    max_retries = 10  
    for i in range(max_retries):
        try:
            response = client.models.generate_content(model=SELECT_MODEL, contents=prompt)
            return response.text
        except Exception as e:
            if i < max_retries - 1:
                time.sleep(3.0)  # 3秒待ってリトライ
                continue
            else:
                raise e

st.title("🎯 一問一答！面接採点AI")
st.caption("あなたの回答をその場でガチ採点＆即修正する特化型ツール")

# --- ステップ1: 日記（テーマ）の入力 ---
if st.session_state.step == "input_diary":
    st.subheader("1. 今日、頑張ったことや取り組んだことは？")
    user_initial = st.text_input("エピソードを1行で入力", placeholder="例：スマホアプリの公開設定をやりきった！")

    if st.button("質問を生成する", type="primary"):
        if user_initial.strip() != "":
            with st.spinner("面接官が深掘り質問を考えています..."):
                prompt = (
                    f"あなたは採用面接官です。学生から「{user_initial}」という取り組みを聞きました。\n"
                    "この内容をガクチカとして深掘りするための、鋭い質問を1つだけ作成してください。\n"
                    "前置きや挨拶は一切抜きで、質問のセリフだけを出力してください。"
                )
                try:
                    # ちゃんと再試行関数を使う
                    question = generate_with_retry(prompt)
                    st.session_state.diary_theme = user_initial
                    st.session_state.ai_question = question
                    st.session_state.step = "answer_question"
                    st.rerun()
                except:
                    st.error("Googleのサーバーが極度に混み合っています。少し時間を置いて再度お試しください。")

# --- ステップ2: 質問への回答 ---
elif st.session_state.step == "answer_question":
    st.info(f"✨ **今日の日記テーマ:** {st.session_state.diary_theme}")
    
    st.subheader("🗣 面接官からの質問")
    st.markdown(f"🤖 **「{st.session_state.ai_question}」**")
    
    st.write("---")
    
    with st.form(key="answer_form"):
        ans = st.text_area("あなたの回答を入力してください：", placeholder="例：〇〇という課題があったので、××という工夫をして解決しました。", height=120)
        submit = st.form_submit_button(label="この回答で採点する！", type="primary")
        
    if submit:
        if ans.strip() != "":
            with st.spinner("採点中... 評価シートを作成しています..."):
                score_prompt = (
                    f"面接のテーマ: {st.session_state.diary_theme}\n"
                    f"面接官の質問: {st.session_state.ai_question}\n"
                    f"学生の回答: {ans}\n\n"
                    "上記を踏まえ、学生の回答を厳しく、かつ具体的なアドバイスを交えて採点してください。\n"
                    "スマホで見やすくなるよう、長文は避け、必ず以下のフォーマット（絵文字含む）通りに出力してください。\n\n"
                    "💯 【得点】: 〇〇点 / 100点\n\n"
                    "👍 【良かったところ】\n"
                    "・（ここに箇条書きで1点）\n\n"
                    "⚠️ 【悪かったところ・足りない視点】\n"
                    "・（ここに箇条書きで1点）\n\n"
                    "✨ 【こう直すともっと響く！修正案】\n"
                    "「（ここに面接官を唸らせる具体的な模範解答の文章）」"
                )
                try:
                    # 🔧 ここが抜けていたので、しっかり generate_with_retry に修正しました！
                    result_text = generate_with_retry(score_prompt)
                    st.session_state.user_answer = ans
                    st.session_state.score_result = result_text
                    st.session_state.step = "show_result"
                    st.rerun()
                except:
                    st.error("Googleのサーバーが極度に混み合っています。少し時間を置いて再度お試しください。")

# --- ステップ3: 採点結果の表示 ---
elif st.session_state.step == "show_result":
    st.success("🎉 採点完了！結果が出ました")
    
    st.text_container = st.container(border=True)
    with st.text_container:
        st.markdown(f"**テーマ:** {st.session_state.diary_theme}")
        st.markdown(f"**質問:** {st.session_state.ai_question}")
        st.markdown(f"**あなたの回答:** {st.session_state.user_answer}")
    
    st.write("---")
    
    st.markdown("### 📊 AI面接官のガチ評価シート")
    st.info(st.session_state.score_result)
    
    st.write("")
    
    if st.button("🔄 もう一度別のテーマで練習する", type="secondary"):
        st.session_state.step = "input_diary"
        st.session_state.diary_theme = ""
        st.session_state.ai_question = ""
        st.session_state.user_answer = ""
        st.session_state.score_result = ""
        st.rerun()