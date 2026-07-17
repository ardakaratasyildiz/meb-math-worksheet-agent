"""tablo_sorusu {{table:...}} direktifi → kusursuz GFM markdown testleri.

grafik/örüntü deseninin tablo karşılığı: LLM ham markdown yazmaz (2.5-flash bozuk
üretiyordu), direktif verir; sistem hizalı/ayraç-satırlı GFM üretir → mevcut PDF +
frontend render yolu aynen çalışır.
"""
from app.services.svg_utils import process_table_directives


def test_basic_table_directive():
    out = process_table_directives(
        "Tablo: {{table: Şehir | Nüfus ;; Şehir A | 8040205 ;; Şehir B | 80400025}}"
    )
    assert "{{table" not in out  # tüketildi
    assert "| Şehir | Nüfus |" in out
    assert "|---|---|" in out
    assert "| Şehir A | 8040205 |" in out
    assert "| Şehir B | 80400025 |" in out


def test_ragged_rows_normalized():
    # 2. satırda eksik hücre, 3. satırda fazla → başlık sütun sayısına eşitlenir.
    out = process_table_directives("{{table: A | B | C ;; 1 | 2 ;; 4 | 5 | 6 | 7}}")
    lines = [l for l in out.splitlines() if l.strip().startswith("|")]
    # header + separator + 2 data = 4 satır; hepsi 3 sütun (2 pipe içi + kenarlar).
    for l in lines:
        assert l.count("|") == 4  # 3 hücre → 4 pipe
    assert "| 1 | 2 |  |" in out  # eksik hücre boş dolduruldu


def test_pipe_in_cell_escaped():
    out = process_table_directives("{{table: A | B ;; x\\|y | z}}")
    # kullanıcı zaten \| yazmışsa bozulmamalı; render geçerli tablo üretmeli
    assert "|---|---|" in out


def test_malformed_is_noop():
    # Tek satır (başlık yok/veri yok) veya tek sütun → orijinali koru.
    assert process_table_directives("{{table: sadece bir satır}}") == "{{table: sadece bir satır}}"
    one_col = "{{table: A ;; 1 ;; 2}}"
    assert process_table_directives(one_col) == one_col


def test_block_separation():
    # Tablo blok-seviye parse edilsin diye önü/arkası boş satırla sarılmalı.
    out = process_table_directives("Öncesi.{{table: A | B ;; 1 | 2}}Sonrası.")
    assert "Öncesi.\n\n|" in out
    assert "|\n\nSonrası." in out


def test_user_example_three_cities():
    out = process_table_directives(
        "{{table: Şehir | Nüfus (Okunuşu) ;; "
        "Şehir A | Sekiz milyon kırk bin iki yüz beş ;; "
        "Şehir B | Seksen milyon dört yüz bin yirmi beş ;; "
        "Şehir C | Sekiz yüz milyon kırk bin yirmi beş}}"
    )
    assert out.count("| Şehir | Nüfus (Okunuşu) |") == 1  # başlık tek
    assert "| Şehir A | Sekiz milyon kırk bin iki yüz beş |" in out
    assert "| Şehir C | Sekiz yüz milyon kırk bin yirmi beş |" in out


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
