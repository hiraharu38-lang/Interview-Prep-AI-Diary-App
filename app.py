import streamlit as st
from google import genai
import time

st.set_page_config(
    page_title="面接対策AI日記",
    page_icon="📝",
    layout="centered"
)

# 3.1 flash-lite で安定爆速化
SELECT_MODEL = 'gemini-3.1-flash-lite'

# APIの初期化
api_key = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=api_key)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 10回全滅するまでは絶対に大元にエラーを漏らさない関数
def generate_with_retry(prompt):
    max_retries = 10  
    for i in range(max_retries):
        try:
            response = client.models.generate_content(model=SELECT_MODEL, contents=prompt)
            return response.text
        except Exception as e:
            if i < max_retries - 1:
                time.sleep(5.0)
                continue
            else:
                raise e

st.title("📝 面接対策AI日記")
st.caption("日々の出来事をガクチカ・自己分析に変換する、あなた専用の面接官")

# 対話が始まっていない時だけ、最初の入力欄を表示
if len(st.session_state.chat_history) < 2:
    st.subheader("1. 今日、頑張ったことや取り組んだことは？")
    user_initial = st.text_input("最初のエピソードを入力（1行メモでOK）", placeholder="例：スマホアプリを制作した", key="initial_input")

    if st.button("面接スタート", type="primary"):
        if user_initial.strip() != "":
            success = False
            with st.spinner("面接官が質問を考えています..."):
                # 【プロンプト修正】余計な枕詞を完全に禁止
                prompt = (
                    f"あなたは企業の採用面接官です。学生から「{user_initial}」という今日の取り組みを聞きました。\n"
                    "このエピソードをガクチカとして深掘りするための、鋭い質問を1つだけ作成してください。\n"
                    "【重要ルール】「質問をご提案します」などの前置きや解説、挨拶は一切不要です。"
                    "「」などの括弧も使わず、面接官がその場で学生に問いかけるセリフ（テキスト）だけを出力してください。"
                )
                try:
                    ai_text = generate_with_retry(prompt)
                    st.session_state.chat_history = [
                        {"role": "user", "text": user_initial},
                        {"role": "model", "text": ai_text}
                    ]
                    success = True
                except:
                    st.error("Googleのサーバーが極度に混み合っています。少し時間を置いて再度お試しください。")
            
            if success:
                st.rerun()

# 完全にAIの回答がセットされている場合のみ対話画面を表示
if len(st.session_state.chat_history) >= 2:
    st.write("---")
    
    # 一番上に日記エピソードを常にピン留め表示
    initial_diary = st.session_state.chat_history[0]["text"]
    st.info(f"✨ **今日の日記テーマ:** {initial_diary}")
    
    st.subheader("🗣 面接官との対話")
    
    # 過去の履歴を表示
    for msg in st.session_state.chat_history[1:]:
        if msg["role"] == "model":
            st.markdown(f"🤖 **面接官:** {msg['text']}")
        else:
            st.markdown(f"👤 **あなた:** {msg['text']}")
    
    st.write("")
    
    with st.form(key="reply_form", clear_on_submit=True):
        user_reply = st.text_area("面接官の質問に対するあなたの回答を入力：", height=100)
        submit_button = st.form_submit_button(label="回答を送信する")

    advice_button = st.button("💡 模範解答・アドバイスを貰う")
    
    # --- 送信ボタンが押された時の処理 ---
    if submit_button:
        if user_reply.strip() != "":
            chat_context = ""
            for m in st.session_state.chat_history:
                speaker = "学生" if m["role"] == "user" else "面接官"
                chat_context += f"{speaker}: {m['text']}\n"
            chat_context += f"学生: {user_reply}\n"
            
            # 【プロンプト修正】ここでも余計な解説を徹底的に排除
            prompt = (
                f"これまでの面接のやり取りは以下の通りです：\n{chat_context}\n\n"
                "これに対する次の深掘り質問を1つだけ作成してください。\n"
                "【重要ルール】「回答ありがとうございます」や「〜という意図を込めています」などの前置き・解説は一切禁止します。"
                "面接官の純粋な質問のセリフ（テキスト）だけを1文〜2文で出力してください。"
            )
            
            success = False
            with st.spinner("面接官が考えています..."):
                try:
                    ai_text = generate_with_retry(prompt)
                    st.session_state.chat_history.append({"role": "user", "text": user_reply})
                    st.session_state.chat_history.append({"role": "model", "text": ai_text})
                    success = True
                except:
                    st.error("Googleのサーバーが極度に混み合っています。少し時間を置いて再度お試しください。")
            
            if success:
                st.rerun()
                
    # --- アドバイスボタンが押された時の処理 ---
    if advice_button:
        chat_context = ""
        for m in st.session_state.chat_history:
            speaker = "学生" if m["role"] == "user" else "面接官"
            chat_context += f"{speaker}: {m['text']}\n"
            
        # 【プロンプト修正】簡潔で見やすいアドバイスを要求
        advice_prompt = (
            f"これまでの面接のやり取りを元に、学生へのフィードバックを作成してください。\n\n"
            f"【やり取り】\n{chat_context}\n\n"
            "【出力ルール】\n"
            "スマホで見やすくなるよう、長文は避け、以下の3つのセクションに分けて簡潔に箇条書きなどで出力してください。\n"
            "1. 🎯 今回の回答の評価（良かった点・足りない視点を1文で）\n"
            "2. 🌟 模範解答（面接官を「おっ」と言わせる文章の具体例）\n"
            "3. 💡 ワンポイントアドバイス（次のステップへの改善点）"
        )
        
        with st.spinner("アドバイザーが模範解答を執筆中..."):
            try:
                ai_text = generate_with_retry(advice_prompt)
                st.markdown("### 🌟 AI面接官からの模範解答・アドバイス")
                st.info(ai_text)
            except:
                st.error("Googleのサーバーが極度に混み合っています。少し時間を置いて再度お試しください。")