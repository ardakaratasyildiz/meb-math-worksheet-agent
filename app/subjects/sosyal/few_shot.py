"""Sosyal Bilgiler few-shot havuzu — sınıf → kazanım kodu → örnekler.

MVP: BOŞ. Güçlü system prompt (tarihsel doğruluk + tip formatları) ile metin-tabanlı
sorular few-shot olmadan da yüksek kalitede çıkıyor (Fen/İngilizce deneyimi). Gerçek
few-shot (EBA örnek soruları + Sozel_LGS İnkılap bölümü, cevap anahtarlı) sonraki
kalite adımında çıkarılacak.

Yapı Fen ile aynı: dict[grade][kazanim_kod] -> [{type, difficulty, question, answer, solution, source}].
"""
from __future__ import annotations

SOS_EXAMPLES: dict[int, dict[str, list[dict]]] = {}
