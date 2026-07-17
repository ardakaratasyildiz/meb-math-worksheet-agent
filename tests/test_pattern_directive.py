"""oruntu_sekil {{pattern:...}} direktifi → deterministik SVG testleri.

grafik_okuma'nın {{chart}} deseninin örüntü karşılığı: LLM ham SVG çizmez, direktif
verir, sistem güvenilir SVG üretir (A/B: ham SVG iki modelde de düşük-yield idi).
"""
from app.services.svg_utils import (
    is_dangerous,
    is_valid_svg,
    process_pattern_directives,
)


def test_sequence_directive_renders_svg():
    out = process_pattern_directives(
        "Örüntü: {{pattern:daire#kirmizi, kare#mavi, ucgen#yesil, daire#kirmizi, ?}}"
    )
    assert "<svg" in out and "</svg>" in out
    assert "{{pattern" not in out  # direktif tüketildi
    assert "<circle" in out and "<rect" in out and "<polygon" in out
    assert ">?</text>" in out  # eksik slot
    assert "#ef4444" in out and "#3b82f6" in out  # kirmizi, mavi çözüldü
    ok, reason = is_valid_svg(out[out.index("<svg"):out.index("</svg>") + 6])
    assert ok, reason
    assert not is_dangerous(out)


def test_seq_prefix_optional():
    a = process_pattern_directives("{{pattern:daire, kare, ?}}")
    b = process_pattern_directives("{{pattern:seq|daire, kare, ?}}")
    assert "<svg" in a and "<svg" in b


def test_growing_dots_directive():
    out = process_pattern_directives("Devam ettir: {{pattern:grow|1,3,5,?}}")
    assert "<svg" in out and out.count("<circle") == 1 + 3 + 5  # 9 nokta
    assert ">?</text>" in out
    ok, _ = is_valid_svg(out[out.index("<svg"):out.rindex("</svg>") + 6])
    assert ok


def test_unknown_color_falls_back_to_palette():
    out = process_pattern_directives("{{pattern:daire#bilinmeyenrenk, kare, ?}}")
    assert "<svg" in out  # bozulmadan render


def test_malformed_or_empty_is_noop():
    # Şekil yok / sadece ? → orijinali koru (veri metinde kalır).
    txt = "{{pattern:?}}"
    assert process_pattern_directives(txt) == txt
    txt2 = "{{pattern:   }}"
    assert process_pattern_directives(txt2) == txt2


def test_star_and_diamond_shapes():
    out = process_pattern_directives("{{pattern:yildiz#sari, elmas#mor, ?}}")
    assert "<polygon" in out  # yıldız + elmas polygon ile çizilir
    assert "#f59e0b" in out and "#8b5cf6" in out


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
