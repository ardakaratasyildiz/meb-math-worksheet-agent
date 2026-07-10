"""İngilizce few-shot örnek havuzu — sınıf → kazanım kodu → örnekler.

MVP: BOŞ. Fen deneyimi gösterdi ki güçlü system prompt + seviye kuralları ile
metin-tabanlı sorular few-shot olmadan da yüksek kalitede çıkıyor; İngilizce MC
desenleri prompt'a (QUESTION_ANALYSIS'ten) zaten damıtıldı. Gerçek few-shot
(EBA ünite örnek soruları 8 + Sozel_LGS İngilizce bölümü, cevap anahtarlı) bir
sonraki kalite adımında çıkarılacak (Fen few-shot deseni: metin-çıkar → doğrula →
kazanıma etiketle; 5-7 için TYMM crosswalk — QUESTION_ANALYSIS §6).

Yapı Fen ile aynı: dict[grade][kazanim_kod] -> [{type, difficulty, question, answer, solution, source}].
"""
from __future__ import annotations

# Sınıf → kazanım kodu → örnek listesi. Boş → collect_few_shot [] döner (RAG yok).
ING_EXAMPLES: dict[int, dict[str, list[dict]]] = {}
