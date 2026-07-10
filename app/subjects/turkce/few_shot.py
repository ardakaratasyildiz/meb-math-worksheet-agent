"""Türkçe few-shot havuzu — sınıf → kazanım kodu → örnekler.

MVP: BOŞ. Güçlü system prompt (özgün pasaj + nesnellik + dil kuralı) ile metin-tabanlı
sorular few-shot olmadan da üretilebiliyor (Fen/İngilizce/Sosyal deneyimi). Gerçek
few-shot (LGS sözel Türkçe bölümü + EBA örnek soruları) sonraki kalite adımında.

Yapı: dict[grade][kazanim_kod] -> [{type, difficulty, question, answer, solution, source}].
"""
from __future__ import annotations

TR_EXAMPLES: dict[int, dict[str, list[dict]]] = {}
