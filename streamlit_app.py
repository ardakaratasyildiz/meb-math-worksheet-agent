"""MEB Matematik Çalışma Kağıdı Üretici — Streamlit arayüzü.

Bu uygulama FastAPI backend'ini HTTP üzerinden çağırır.
Backend'i önce çalıştırın: `uvicorn app.main:app --reload`
Sonra: `streamlit run streamlit_app.py`
"""
import os
from datetime import datetime
from typing import Any

import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
DEFAULT_TIMEOUT = 180

DIFFICULTIES = [("kolay", "Kolay"), ("orta", "Orta"), ("zor", "Zor")]

st.set_page_config(
    page_title="MEB Matematik Çalışma Kağıdı Üretici",
    page_icon="📐",
    layout="wide",
)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_grades() -> list[dict]:
    r = requests.get(f"{API_BASE}/api/curriculum/grades", timeout=10)
    r.raise_for_status()
    return r.json()["grades"]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_topics(grade_id: int) -> list[dict]:
    r = requests.get(
        f"{API_BASE}/api/curriculum/grades/{grade_id}/topics", timeout=10
    )
    r.raise_for_status()
    return r.json()["topics"]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_kazanimlar(grade_id: int, topic_id: str) -> list[dict]:
    r = requests.get(
        f"{API_BASE}/api/curriculum/grades/{grade_id}/topics/{topic_id}/kazanimlar",
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["kazanimlar"]


def generate_worksheet(payload: dict[str, Any]) -> dict:
    r = requests.post(
        f"{API_BASE}/api/worksheets/generate",
        json=payload,
        timeout=DEFAULT_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=600, show_spinner="PDF hazırlanıyor...")
def render_pdf(worksheet: dict) -> bytes:
    """Mevcut worksheet JSON'unu backend'de PDF'e çevirir (LLM çağrısı yok)."""
    r = requests.post(
        f"{API_BASE}/api/worksheets/render.pdf",
        json=worksheet,
        timeout=30,
    )
    r.raise_for_status()
    return r.content


def _check_backend() -> bool:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=3)
        return r.status_code == 200
    except requests.RequestException:
        return False


st.title("📐 MEB Matematik Çalışma Kağıdı Üretici")
st.caption("MEB müfredatına uygun (1-7. sınıf) matematik soruları — Gemini destekli")

backend_ok = _check_backend()
if not backend_ok:
    st.error(
        f"❌ FastAPI backend çalışmıyor (`{API_BASE}`). "
        "Önce bir terminalde `uvicorn app.main:app --reload` komutunu çalıştırın."
    )
    st.stop()
else:
    st.success(f"✅ Backend aktif: `{API_BASE}`")

with st.sidebar:
    st.header("Seçenekler")

    try:
        grades = fetch_grades()
    except Exception as exc:
        st.error(f"Sınıflar yüklenemedi: {exc}")
        st.stop()

    grade = st.selectbox(
        "Sınıf",
        options=[g["id"] for g in grades],
        format_func=lambda gid: next(
            f"{g['name']} ({g['level']})" for g in grades if g["id"] == gid
        ),
    )

    try:
        topics = fetch_topics(grade)
    except Exception as exc:
        st.error(f"Konular yüklenemedi: {exc}")
        st.stop()

    if not topics:
        st.warning("Bu sınıf için konu bulunamadı.")
        st.stop()

    topic_id = st.selectbox(
        "Konu",
        options=[t["id"] for t in topics],
        format_func=lambda tid: next(
            f"{t['name']} ({t['kazanim_count']} kazanım)"
            for t in topics
            if t["id"] == tid
        ),
    )

    try:
        kazanimlar = fetch_kazanimlar(grade, topic_id)
    except Exception as exc:
        st.error(f"Kazanımlar yüklenemedi: {exc}")
        st.stop()

    kazanim_options = ["__AUTO__"] + [k["kod"] for k in kazanimlar]

    def _fmt_kazanim(k: str) -> str:
        if k == "__AUTO__":
            return "Tüm kazanımlar (otomatik dağılım)"
        metin = next(x["metin"] for x in kazanimlar if x["kod"] == k)
        return f"{k} — {metin[:70]}{'...' if len(metin) > 70 else ''}"

    kazanim_kod = st.selectbox(
        "Kazanım",
        options=kazanim_options,
        format_func=_fmt_kazanim,
    )

    difficulty = st.radio(
        "Zorluk",
        options=[d[0] for d in DIFFICULTIES],
        format_func=lambda d: dict(DIFFICULTIES)[d],
        horizontal=True,
        index=1,
    )

    question_count = st.slider(
        "Soru Sayısı", min_value=1, max_value=20, value=10, step=1
    )

    generate_btn = st.button(
        "🚀 Soruları Üret", type="primary", use_container_width=True
    )


col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("Seçim Özeti")
    selected_topic = next(t for t in topics if t["id"] == topic_id)
    st.markdown(
        f"""
- **Sınıf:** {grade}. Sınıf
- **Konu:** {selected_topic["name"]}
- **Kazanım:** {"Tümü (otomatik dağılım)" if kazanim_kod == "__AUTO__" else kazanim_kod}
- **Zorluk:** {dict(DIFFICULTIES)[difficulty]}
- **Soru Sayısı:** {question_count}
"""
    )

with col2:
    st.subheader("Bu Konunun Kazanımları")
    for k in kazanimlar:
        st.markdown(f"**{k['kod']}** — {k['metin']}")

st.divider()

if generate_btn:
    payload = {
        "grade": grade,
        "topic_id": topic_id,
        "difficulty": difficulty,
        "question_count": question_count,
    }
    if kazanim_kod != "__AUTO__":
        payload["kazanim_kod"] = kazanim_kod

    with st.spinner("Gemini'den sorular isteniyor... (ilk denemede 503 alınırsa fallback modellere geçilir)"):
        try:
            data = generate_worksheet(payload)
        except requests.HTTPError as exc:
            body = exc.response.text if exc.response is not None else str(exc)
            st.error(f"❌ API hatası: {body}")
            st.stop()
        except Exception as exc:
            st.error(f"❌ Beklenmeyen hata: {exc}")
            st.stop()

    ws = data["worksheet"]
    meta = data["metadata"]

    st.success(f"✅ {ws['question_count']} soru üretildi — {meta['model']} ile")

    with st.expander("📋 Metadata", expanded=False):
        st.json(meta)

    st.header(ws["title"])
    st.caption(
        f"Konu: {ws['topic']} • Zorluk: {ws['difficulty'].capitalize()} • "
        f"Soru Sayısı: {ws['question_count']}"
    )

    tab_questions, tab_answer_key, tab_raw = st.tabs(
        ["📝 Sorular", "🔑 Cevap Anahtarı", "🧾 Ham JSON"]
    )

    with tab_questions:
        for q in ws["questions"]:
            with st.container(border=True):
                head_cols = st.columns([1, 5, 2])
                head_cols[0].markdown(f"### {q['number']}")
                head_cols[1].markdown(" ")  # spacer
                head_cols[2].markdown(
                    f"🏷️ `{q['question_type']}`  \n"
                    f"📖 `{q['kazanim_kod']}`"
                )
                # Soru gövdesi: Markdown (tablo, kod bloğu, ASCII şekil dahil) korunur.
                st.markdown(q["question"])
                with st.expander("💡 Çözüm / Cevap", expanded=False):
                    st.markdown(f"**Cevap:** {q['answer']}")
                    st.markdown(f"**Çözüm:** {q['solution_steps']}")

    with tab_answer_key:
        for entry in ws["answer_key"]:
            st.markdown(f"**{entry['number']}.** {entry['answer']}")

    with tab_raw:
        st.json(data)

    export_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dl_cols = st.columns(2)
    with dl_cols[0]:
        st.download_button(
            "⬇️ JSON olarak indir",
            data=str(data).encode("utf-8"),
            file_name=f"worksheet_{grade}_{topic_id}_{export_ts}.json",
            mime="application/json",
            use_container_width=True,
        )
    with dl_cols[1]:
        try:
            pdf_bytes = render_pdf(ws)
            st.download_button(
                "📄 PDF olarak indir",
                data=pdf_bytes,
                file_name=f"worksheet_{grade}_{topic_id}_{export_ts}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except requests.HTTPError as exc:
            st.error(f"PDF üretilemedi: {exc.response.text if exc.response else exc}")
        except Exception as exc:
            st.error(f"PDF üretilemedi: {exc}")
else:
    st.info("👈 Sol panelden seçimlerinizi yapın ve **Soruları Üret** butonuna tıklayın.")
