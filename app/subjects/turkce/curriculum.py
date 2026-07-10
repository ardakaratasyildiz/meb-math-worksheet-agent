"""Türkçe müfredatı — 2024 TYMM, PRAGMATİK MODEL (yarı-otomatik).

Üniteler = TEMA'lar (programdan çıkarıldı). Kazanımlar = sınıf düzeyi çekirdek
yetkinlikler (okuma-anlama/sözcük/cümle/yazım/noktalama/metin/yazma — kısmen elle)
+ DYS dil bilgisi (programdan çıkarıldı). Her tema sınıfın kazanım setini paylaşır
(GRADE_KAZANIMLAR referansı). Bkz. scripts/derive_turkce_curriculum.py, SOZEL_DERSLER_PLAN.md.
"""
from __future__ import annotations

from typing import NotRequired, TypedDict


class TrKazanim(TypedDict):
    kod: str
    metin: str
    difficulty_hints: NotRequired[dict[str, str]]


class TrUnit(TypedDict):
    unit_id: str
    grade: int
    no: int
    name: str
    kazanimlar: list[TrKazanim]


GRADE_KAZANIMLAR: dict[int, list[TrKazanim]] = {
    1: [
        {"kod": 'TR.1.OKA.1', "metin": 'Okuduğu/dinlediği metnin konusunu ve ana duygusunu/ana fikrini belirler.'},
        {"kod": 'TR.1.OKA.2', "metin": 'Metindeki olayları oluş sırasına göre sıralar ve neden-sonuç ilişkisi kurar.'},
        {"kod": 'TR.1.SOZ.1', "metin": 'Bağlamdan hareketle bilmediği sözcüklerin anlamını tahmin eder; eş/zıt anlamı bulur.'},
        {"kod": 'TR.1.YAZ.1', "metin": 'Büyük harf ve yazım kurallarını (ör. özel ad, gün/ay) doğru uygular.'},
        {"kod": 'TR.1.NOK.1', "metin": 'Nokta, virgül, soru işareti gibi temel noktalama işaretlerini yerinde kullanır.'},
        {"kod": 'TR.1.YZM.1', "metin": 'Görsel/konu üzerine kısa, anlamlı ve düzenli bir metin yazar.'},
    ],
    2: [
        {"kod": 'TR.2.OKA.1', "metin": 'Okuduğu/dinlediği metnin konusunu ve ana duygusunu/ana fikrini belirler.'},
        {"kod": 'TR.2.OKA.2', "metin": 'Metindeki olayları oluş sırasına göre sıralar ve neden-sonuç ilişkisi kurar.'},
        {"kod": 'TR.2.SOZ.1', "metin": 'Bağlamdan hareketle bilmediği sözcüklerin anlamını tahmin eder; eş/zıt anlamı bulur.'},
        {"kod": 'TR.2.YAZ.1', "metin": 'Büyük harf ve yazım kurallarını (ör. özel ad, gün/ay) doğru uygular.'},
        {"kod": 'TR.2.NOK.1', "metin": 'Nokta, virgül, soru işareti gibi temel noktalama işaretlerini yerinde kullanır.'},
        {"kod": 'TR.2.YZM.1', "metin": 'Görsel/konu üzerine kısa, anlamlı ve düzenli bir metin yazar.'},
    ],
    3: [
        {"kod": 'TR.3.OKA.1', "metin": 'Okuduğu/dinlediği metnin konusunu ve ana duygusunu/ana fikrini belirler.'},
        {"kod": 'TR.3.OKA.2', "metin": 'Metindeki olayları oluş sırasına göre sıralar ve neden-sonuç ilişkisi kurar.'},
        {"kod": 'TR.3.SOZ.1', "metin": 'Bağlamdan hareketle bilmediği sözcüklerin anlamını tahmin eder; eş/zıt anlamı bulur.'},
        {"kod": 'TR.3.YAZ.1', "metin": 'Büyük harf ve yazım kurallarını (ör. özel ad, gün/ay) doğru uygular.'},
        {"kod": 'TR.3.NOK.1', "metin": 'Nokta, virgül, soru işareti gibi temel noktalama işaretlerini yerinde kullanır.'},
        {"kod": 'TR.3.YZM.1', "metin": 'Görsel/konu üzerine kısa, anlamlı ve düzenli bir metin yazar.'},
    ],
    4: [
        {"kod": 'TR.4.OKA.1', "metin": 'Okuduğu/dinlediği metnin konusunu ve ana duygusunu/ana fikrini belirler.'},
        {"kod": 'TR.4.OKA.2', "metin": 'Metindeki olayları oluş sırasına göre sıralar ve neden-sonuç ilişkisi kurar.'},
        {"kod": 'TR.4.SOZ.1', "metin": 'Bağlamdan hareketle bilmediği sözcüklerin anlamını tahmin eder; eş/zıt anlamı bulur.'},
        {"kod": 'TR.4.YAZ.1', "metin": 'Büyük harf ve yazım kurallarını (ör. özel ad, gün/ay) doğru uygular.'},
        {"kod": 'TR.4.NOK.1', "metin": 'Nokta, virgül, soru işareti gibi temel noktalama işaretlerini yerinde kullanır.'},
        {"kod": 'TR.4.YZM.1', "metin": 'Görsel/konu üzerine kısa, anlamlı ve düzenli bir metin yazar.'},
    ],
    5: [
        {"kod": 'TR.5.OKA.1', "metin": 'Metnin konusunu, ana fikrini ve yardımcı fikirlerini belirler.'},
        {"kod": 'TR.5.OKA.2', "metin": 'Metinden hareketle çıkarımda bulunur; başlık, akış ve bölümleri yorumlar.'},
        {"kod": 'TR.5.OKA.3', "metin": 'Metindeki olay/bilgi akışını, neden-sonuç ve amaç-sonuç ilişkilerini çözümler.'},
        {"kod": 'TR.5.SOZ.1', "metin": 'Sözcüğün gerçek, mecaz, terim ve yan anlamını bağlamdan belirler.'},
        {"kod": 'TR.5.SOZ.2', "metin": 'Deyim, atasözü ve söz gruplarının anlamını ve metne katkısını açıklar.'},
        {"kod": 'TR.5.CUM.1', "metin": 'Cümlede anlam ilişkilerini (neden-sonuç, koşul, karşılaştırma, öznel-nesnel) belirler.'},
        {"kod": 'TR.5.SAN.1', "metin": 'Metindeki söz sanatlarını ve anlatım biçimlerini (betimleme, öyküleme vb.) belirler.'},
        {"kod": 'TR.5.MET.1', "metin": 'Metin türünü (öykü, şiir, deneme, haber, bilgilendirici vb.) özelliklerinden tanır.'},
        {"kod": 'TR.5.YAZ.1', "metin": 'Yazım kurallarını (büyük harf, birleşik/ayrı yazım, sayıların yazımı vb.) doğru uygular.'},
        {"kod": 'TR.5.NOK.1', "metin": 'Noktalama işaretlerini işlevine uygun ve doğru kullanır.'},
        {"kod": 'TR.5.YZM.1', "metin": 'Bir konuda planlı, tutarlı ve tür özelliklerine uygun bir metin/paragraf yazar.'},
        {"kod": 'DYS.DO.5.1', "metin": 'İsim ve fiili ayırt eder'},
        {"kod": 'DYS.DO.5.2', "metin": 'İsmin tür özelliklerini ayırt eder'},
        {"kod": 'DYS.KY.5.1', "metin": 'İsmi tür özelliklerine uygun kullanır'},
        {"kod": 'DYS.DO.5.3', "metin": 'İsmin yerine tercih edilen söz varlığını ve işlevlerini belirler'},
        {"kod": 'DYS.KY.5.2', "metin": 'İsmin yerine kullanılan söz varlığını anlatımı zenginleştirecek şekilde işlevine uygun olarak kullanır'},
        {"kod": 'DYS.DO.5.4', "metin": 'İsimleri çeşitli özellikleri bakımından niteleyen ve belirten söz varlığını/dil yapılarını belirler'},
        {"kod": 'DYS.KY.5.3', "metin": 'İsimleri çeşitli özellikleri bakımından niteleyen ve belirten söz varlığını/dil yapılarını kullanır'},
        {"kod": 'DYS.DO.5.5', "metin": 'Karşılaştırma işlevli söz varlığını/dil yapılarını (ama, fakat, daha, en, kadar, -DAn çok, -DAn az vb.) belirler'},
        {"kod": 'DYS.KY.5.4', "metin": 'Karşılaştırma işlevli söz varlığını/dil yapılarını (ama, fakat, daha, en, kadar, -DAn çok, -DAn az vb.) kullanır'},
        {"kod": 'DYS.DO.5.6', "metin": 'Benzerlik işlevli söz varlığını (gibi, tıpkı, tıpkı… gibi, sanki, aynen vb.) belirler'},
        {"kod": 'DYS.KY.5.5', "metin": 'Benzerlik işlevli söz varlığını (gibi, tıpkı, tıpkı… gibi, sanki, aynen vb.) kullanır'},
        {"kod": 'DYS.DO.5.7', "metin": 'Özetleme işlevli söz varlığını/dil yapılarını (açıkçası, yani, özetle, kısacası, özet olarak, uzun lafın kısası, sonuç olarak vb.) belirler'},
        {"kod": 'DYS.KY.5.6', "metin": 'Özetleme işlevli söz varlığını/dil yapılarını (açıkçası, yani, özetle, kısacası, özet olarak, uzun lafın kısası, sonuç olarak vb.) kullanır'},
        {"kod": 'DYS.DO.5.8', "metin": 'Dinlediklerinde/izlediklerinde ve okuduklarında Türkçenin doğru, güzel ve etkili kullanıldığı cümleleri belirler'},
        {"kod": 'DYS.KY.5.7', "metin": 'Türkçenin doğru, güzel ve etkili kullanıldığı cümleler kurar'},
        {"kod": 'DYS.KY.5.8', "metin": 'Gereksiz kelimelere yer vermeden cümleler kurar. 3. EKLER 225 ORTAOKUL TÜRKÇE DERSİ ÖĞRETİM PROGRAMI ANLAMA ANLATMA İşlev temelli dil yapıları ve söz…'},
    ],
    6: [
        {"kod": 'TR.6.OKA.1', "metin": 'Metnin konusunu, ana fikrini ve yardımcı fikirlerini belirler.'},
        {"kod": 'TR.6.OKA.2', "metin": 'Metinden hareketle çıkarımda bulunur; başlık, akış ve bölümleri yorumlar.'},
        {"kod": 'TR.6.OKA.3', "metin": 'Metindeki olay/bilgi akışını, neden-sonuç ve amaç-sonuç ilişkilerini çözümler.'},
        {"kod": 'TR.6.SOZ.1', "metin": 'Sözcüğün gerçek, mecaz, terim ve yan anlamını bağlamdan belirler.'},
        {"kod": 'TR.6.SOZ.2', "metin": 'Deyim, atasözü ve söz gruplarının anlamını ve metne katkısını açıklar.'},
        {"kod": 'TR.6.CUM.1', "metin": 'Cümlede anlam ilişkilerini (neden-sonuç, koşul, karşılaştırma, öznel-nesnel) belirler.'},
        {"kod": 'TR.6.SAN.1', "metin": 'Metindeki söz sanatlarını ve anlatım biçimlerini (betimleme, öyküleme vb.) belirler.'},
        {"kod": 'TR.6.MET.1', "metin": 'Metin türünü (öykü, şiir, deneme, haber, bilgilendirici vb.) özelliklerinden tanır.'},
        {"kod": 'TR.6.YAZ.1', "metin": 'Yazım kurallarını (büyük harf, birleşik/ayrı yazım, sayıların yazımı vb.) doğru uygular.'},
        {"kod": 'TR.6.NOK.1', "metin": 'Noktalama işaretlerini işlevine uygun ve doğru kullanır.'},
        {"kod": 'TR.6.YZM.1', "metin": 'Bir konuda planlı, tutarlı ve tür özelliklerine uygun bir metin/paragraf yazar.'},
        {"kod": 'DYS.DO.6.1', "metin": 'Kelimelerin kökünü ve ekini ayırt eder'},
        {"kod": 'DYS.DO.6.2', "metin": 'Söz varlığı ve dil yapılarının birleşmesinde karşılaşılan yardımcı ünsüzlerin (y, ş, s, n) ve ses olaylarının (ünlü düşmesi, ünsüz benzeşmesi, ünsüz…'},
        {"kod": 'DYS.KY.6.1', "metin": 'Ses olaylarına (ünlü düşmesi, ünsüz benzeşmesi, ünsüz yumuşaması, ünlü daralması, ünlü türemesi ve ünsüz türemesi) uğrayan söz varlığı ve dil yapılarını…'},
        {"kod": 'DYS.DO.6.3', "metin": 'Özne-yüklem uyumunu ayırt eder. Öğrencinin özne-yüklem uyumunu sağlamada sorun yaşaması hâlinde öğretmen anlama çalışmalarında bu uyuma dikkat çeker'},
        {"kod": 'DYS.KY.6.2', "metin": 'Özne-yüklem uyumunu dikkate alarak cümleler kurar. Öğrencinin özne-yüklem uyumunu sağlamada sorun yaşaması hâlinde öğretmen tarafından anlama…'},
        {"kod": 'DYS.DO.6.4', "metin": 'Sebep işlevli söz varlığını/dil yapılarını (çünkü, bu nedenle, için, diye, demek, demek ki, -DIğI için, ...-sI yüzünden/sebebiyle, ...-nın…'},
        {"kod": 'DYS.KY.6.3', "metin": 'Sebep işlevli söz varlığını/dil yapılarını (çünkü, bu nedenle, için, diye, demek, demek ki, -DIğI için, ...-sI yüzünden/sebebiyle, ...-nın…'},
        {"kod": 'DYS.DO.6.5', "metin": 'Amaç ifade etme işlevli söz varlığını/dil yapılarını (-mAk için, amacıyla, için, -mAsI için, niye, niçin, diye, üzere vb.) belirler'},
        {"kod": 'DYS.KY.6.4', "metin": 'Amaç ifade etme işlevli söz varlığını/dil yapılarını (-mAk için, amacıyla, için, -mAsI için, niye, niçin, diye, üzere vb.) kullanır'},
        {"kod": 'DYS.DO.6.6', "metin": 'Şart işlevli söz varlığını/dil yapılarını (-sA, ise, -DI mI, -DIkçA, -IncA ama, yalnız, lazım, eğer, şayet, ki, mutlaka, kesinlikle, şu şartla, illa vb.)…'},
        {"kod": 'DYS.KY.6.5', "metin": 'Şart işlevli söz varlığını/dil yapılarını (-sA, ise, -DI mI, -DIkçA, -IncA ama, yalnız, lazım, eğer, şayet, ki, mutlaka, kesinlikle, şu şartla, illa vb.)…'},
        {"kod": 'DYS.DO.6.7', "metin": 'Zıtlık işlevli söz varlığını (ama, fakat, lakin, aksine, ancak, yoksa, aslında, hem ... hem de ..., hâlbuki, tam tersine vb.) belirler'},
        {"kod": 'DYS.KY.6.6', "metin": 'Zıtlık işlevli söz varlığını (ama, fakat, lakin, aksine, ancak, yoksa, aslında, hem ... hem de ..., hâlbuki, tam tersine vb.) kullanır'},
        {"kod": 'DYS.DO.6.8', "metin": 'Olumsuzluk işlevli söz varlığını/dil yapılarını (hayır, yok, asla, değil, olmaz, maalesef, ne yazık ki, -sIz, -mA, -mAz vb.) belirler'},
        {"kod": 'DYS.KY.6.7', "metin": 'Olumsuzluk işlevli söz varlığını/dil yapılarını (hayır, yok, asla, değil, olmaz, maalesef, ne yazık ki, -sIz, -mA, -mAz vb.) kullanır'},
        {"kod": 'DYS.DO.6.9', "metin": 'Karşılaştırma işlevli söz varlığını/dil yapılarını (-DAn daha, ise, işin kötüsü, her ne kadar, nasıl, neredeyse vb.) belirler'},
        {"kod": 'DYS.KY.6.8', "metin": 'Karşılaştırma işlevli söz varlığını/dil yapılarını (-DAn daha, ise, işin kötüsü, her ne kadar, nasıl, neredeyse vb.) kullanır'},
        {"kod": 'DYS.DO.6.10', "metin": 'Benzerlik işlevli söz varlığını/dil yapılarını (âdeta, benzer, benzer şekilde, aynı, aynı şekilde, -mIş gibi, sanki, -msI vb.) belirler'},
        {"kod": 'DYS.KY.6.9', "metin": 'Benzerlik işlevli söz varlığını/dil yapılarını (âdeta, benzer, benzer şekilde, aynı, aynı şekilde, -mIş gibi, sanki, -msI vb.) kullanır'},
        {"kod": 'DYS.DO.6.11', "metin": 'Dinlediklerinde/izlediklerinde ve okuduklarında Türkçenin doğru, güzel ve etkili kullanıldığı cümleler belirler'},
        {"kod": 'DYS.KY.6.10', "metin": 'Türkçenin doğru, güzel ve etkili kullanıldığı cümleler kurar'},
    ],
    7: [
        {"kod": 'TR.7.OKA.1', "metin": 'Metnin konusunu, ana fikrini ve yardımcı fikirlerini belirler.'},
        {"kod": 'TR.7.OKA.2', "metin": 'Metinden hareketle çıkarımda bulunur; başlık, akış ve bölümleri yorumlar.'},
        {"kod": 'TR.7.OKA.3', "metin": 'Metindeki olay/bilgi akışını, neden-sonuç ve amaç-sonuç ilişkilerini çözümler.'},
        {"kod": 'TR.7.SOZ.1', "metin": 'Sözcüğün gerçek, mecaz, terim ve yan anlamını bağlamdan belirler.'},
        {"kod": 'TR.7.SOZ.2', "metin": 'Deyim, atasözü ve söz gruplarının anlamını ve metne katkısını açıklar.'},
        {"kod": 'TR.7.CUM.1', "metin": 'Cümlede anlam ilişkilerini (neden-sonuç, koşul, karşılaştırma, öznel-nesnel) belirler.'},
        {"kod": 'TR.7.SAN.1', "metin": 'Metindeki söz sanatlarını ve anlatım biçimlerini (betimleme, öyküleme vb.) belirler.'},
        {"kod": 'TR.7.MET.1', "metin": 'Metin türünü (öykü, şiir, deneme, haber, bilgilendirici vb.) özelliklerinden tanır.'},
        {"kod": 'TR.7.YAZ.1', "metin": 'Yazım kurallarını (büyük harf, birleşik/ayrı yazım, sayıların yazımı vb.) doğru uygular.'},
        {"kod": 'TR.7.NOK.1', "metin": 'Noktalama işaretlerini işlevine uygun ve doğru kullanır.'},
        {"kod": 'TR.7.YZM.1', "metin": 'Bir konuda planlı, tutarlı ve tür özelliklerine uygun bir metin/paragraf yazar.'},
        {"kod": 'DYS.DO.7.1', "metin": 'Çekim eklerinin işlevlerini ayırt eder. [İsim çekim ekleri (çoğul eki, hâl ekleri, ilgi (tamlayan) eki, iyelik ekleri ve soru eki) üzerinde durulur.] [Fiil…'},
        {"kod": 'DYS.KY.7.1', "metin": 'Çekim eklerini işlevlerine uygun kullanır'},
        {"kod": 'DYS.DO.7.2', "metin": 'Yargının gerçekleşme anını (-mAktA, -(I) yor; şu anda, hâlen şimdi, hâlâ vb.) gerçekleşme anından öncesini [-(I)yor, -(I)yordu, -(I)yormuş, -r, -Ar, -DI,…'},
        {"kod": 'DYS.KY.7.2', "metin": 'Yargının gerçekleşme anını (-mAktA, -(I) yor; şu anda, hâlen şimdi, hâlâ vb.) gerçekleşme anından öncesini [-(I)yor, -(I)yordu, -(I)yormuş, -r, -Ar, -DI,…'},
        {"kod": 'DYS.DO.7.3', "metin": 'Fiilleri çeşitli yönlerden belirten söz varlığının/dil yapılarının cümlenin anlamına katkısını (durum, zaman, yer-yön ve soru) belirler'},
        {"kod": 'DYS.KY.7.3', "metin": 'Fiilleri çeşitli yönlerden belirten söz varlığını/dil yapılarını durum, zaman, yer-yön ve soru işlevlerine uygun kullanır'},
        {"kod": 'DYS.DO.7.4', "metin": 'Zıtlık işlevli söz varlığını/dil yapılarını (oysaki, yalnız, meğerse, -A karşın, gelgelelim, nerde kaldı, zıddına, dahası, her ne kadar ki, -(y)ken, -(n)A…'},
        {"kod": 'DYS.KY.7.4', "metin": 'Zıtlık işlevli söz varlığını/dil yapılarını (oysaki, yalnız, meğerse, -A karşın, gelgelelim, nerde kaldı, zıddına, dahası, her ne kadar ki, -(y)ken, -(n)A…'},
        {"kod": 'DYS.DO.7.5', "metin": 'Sınırlama işlevli söz varlığını/dil yapılarını (-A kadar, -A dek, -A değin, -mAk üzere, sadece, yalnız, ancak, artık, bundan sonra, bir, tek, fakat,…'},
        {"kod": 'DYS.KY.7.5', "metin": 'Sınırlama işlevli söz varlığını/dil yapılarını (-A kadar, -A dek, -A değin, -mAk üzere, sadece, yalnız, ancak, artık, bundan sonra, bir, tek, fakat,…'},
        {"kod": 'DYS.DO.7.6', "metin": 'İstek işlevli söz varlığını/dil yapılarını [-sA, -sAnA, -A, -Ar mIsIn, -AyIm, -AlIm, keşke, ne olur, ne olurdu, iste-, talep et-, bari, -AyIm, -AlIm vb.]…'},
        {"kod": 'DYS.KY.7.6', "metin": 'İstek işlevli söz varlığını/dil yapılarını [-sA, -sAnA, -A, -Ar mIsIn, -AyIm, -AlIm, keşke, ne olur, ne olurdu, iste-, talep et-, bari, -AyIm, -AlIm vb.]…'},
        {"kod": 'DYS.DO.7.7', "metin": 'Olumsuzluk işlevli söz varlığını/dil yapılarını (güya, ne fayda, ne fayda ki, ne acı ki, ne gelir elden ki, ne mümkün, ne … ne ..., -mAdAn vb.) belirler'},
        {"kod": 'DYS.KY.7.7', "metin": 'Olumsuzluk işlevli söz varlığını/dil yapılarını (güya, ne fayda, ne fayda ki, ne acı ki, ne gelir elden ki, ne mümkün, ne … ne ..., -mAdAn vb.) kullanır'},
        {"kod": 'DYS.DO.7.8', "metin": 'Dinlediklerinde/izlediklerinde ve okuduklarında Türkçenin doğru, güzel ve etkili kullanıldığı cümleleri belirler'},
        {"kod": 'DYS.KY.7.8', "metin": 'Türkçenin doğru, güzel ve etkili kullanıldığı cümleler kurar'},
        {"kod": 'DYS.DO.7.9', "metin": 'Bir fiilin gerçekleşmesinin gerekli olduğunun söylendiği (-mAlI, -mAsI gerek, -mAnIz gerek, -mAmIz gerek, -mAsI lazım vb.), dilek veya koşul olarak ifade…'},
        {"kod": 'DYS.KY.7.9', "metin": 'Bir fiilin gerçekleşmesinin gerekli olduğunun söylendiği (-mAlI, -mAsI gerek, -mAnIz gerek, -mAmIz gerek, -mAsI lazım vb.), dilek veya koşul olarak ifade…'},
        {"kod": 'DYS.KY.7.10', "metin": 'Anlamca çelişen kelimelere yer vermeden cümleler kurar. 227 ORTAOKUL TÜRKÇE DERSİ ÖĞRETİM PROGRAMI ANLAMA ANLATMA İşlev temelli dil yapıları ve söz…'},
    ],
    8: [
        {"kod": 'TR.8.OKA.1', "metin": 'Metnin konusunu, ana fikrini ve yardımcı fikirlerini belirler.'},
        {"kod": 'TR.8.OKA.2', "metin": 'Metinden hareketle çıkarımda bulunur; başlık, akış ve bölümleri yorumlar.'},
        {"kod": 'TR.8.OKA.3', "metin": 'Metindeki olay/bilgi akışını, neden-sonuç ve amaç-sonuç ilişkilerini çözümler.'},
        {"kod": 'TR.8.SOZ.1', "metin": 'Sözcüğün gerçek, mecaz, terim ve yan anlamını bağlamdan belirler.'},
        {"kod": 'TR.8.SOZ.2', "metin": 'Deyim, atasözü ve söz gruplarının anlamını ve metne katkısını açıklar.'},
        {"kod": 'TR.8.CUM.1', "metin": 'Cümlede anlam ilişkilerini (neden-sonuç, koşul, karşılaştırma, öznel-nesnel) belirler.'},
        {"kod": 'TR.8.SAN.1', "metin": 'Metindeki söz sanatlarını ve anlatım biçimlerini (betimleme, öyküleme vb.) belirler.'},
        {"kod": 'TR.8.MET.1', "metin": 'Metin türünü (öykü, şiir, deneme, haber, bilgilendirici vb.) özelliklerinden tanır.'},
        {"kod": 'TR.8.YAZ.1', "metin": 'Yazım kurallarını (büyük harf, birleşik/ayrı yazım, sayıların yazımı vb.) doğru uygular.'},
        {"kod": 'TR.8.NOK.1', "metin": 'Noktalama işaretlerini işlevine uygun ve doğru kullanır.'},
        {"kod": 'TR.8.YZM.1', "metin": 'Bir konuda planlı, tutarlı ve tür özelliklerine uygun bir metin/paragraf yazar.'},
        {"kod": 'DYS.DO.8.1', "metin": 'Bir adın yerine tercih edilen söz varlığının/ dil yapılarının art ve ön gönderim işlevlerini belirler'},
        {"kod": 'DYS.KY.8.1', "metin": 'Bir adın yerine tercih edilen söz varlığının/ dil yapılarının art ve ön gönderim işlevlerini kullanır'},
        {"kod": 'DYS.DO.8.2', "metin": 'Etken ve edilgen anlatımın anlama olan katkısını belirler. Öğretmen, "Akademik Düşünme Dünyası" temasındaki bilgilendirici metinler üzerinden edilgen…'},
        {"kod": 'DYS.KY.8.3', "metin": 'Etken ve edilgen yapıları işlevine uygun kullanır'},
        {"kod": 'DYS.DO.8.3', "metin": 'Tahminde bulunma işlevli söz varlığını/ dil yapılarını (belki, belki de, sanki, galiba, tahminim, muhtemelen, bence, güya, acaba, dediğine bakılırsa,…'},
        {"kod": 'DYS.DO.8.4', "metin": 'Dinlediklerinde/izlediklerinde ve okuduklarında Türkçenin doğru, güzel ve etkili kullanıldığı cümleleri belirler'},
        {"kod": 'DYS.KY.8.4', "metin": 'Türkçenin doğru, güzel ve etkili kullanıldığı cümleler kurar'},
        {"kod": 'DYS.DO.8.5', "metin": 'Fiilleri ve kendisiyle aynı görevdeki kelime veya kelime gruplarını miktar yönünden belirten söz varlığının/dil yapılarının cümlenin anlamına katkısını belirler'},
        {"kod": 'DYS.KY.8.5', "metin": 'Fiilleri ve kendisiyle aynı görevdeki kelime veya kelime gruplarını miktar yönünden belirten söz varlığının/dil yapılarının cümlenin anlamına katkısını belirler'},
        {"kod": 'DYS.KY.8.6', "metin": 'İfadelerinde söz varlığını (deyim, atasözü, kelime veya kelime grupları) uygun anlamda kullanır'},
        {"kod": 'DYS.KY.8.7', "metin": 'Sıralama, mantık hatası ve anlam belirsizliği içermeyen cümleler kurar. 228 ORTAOKUL TÜRKÇE DERSİ ÖĞRETİM PROGRAMI HAZIRLIK/ISINMA 1. Oyun: 1-2-3-Kendi…'},
    ],
}

_THEMES: dict[int, list[dict]] = {
    1: [
        {"unit_id": 'turkce-1-tema-1-guzel-davranislarimiz', "grade": 1, "no": 1, "name": 'Güzel Davranışlarımız'},
        {"unit_id": 'turkce-1-tema-2-mustafa-kemalden-ataturke', "grade": 1, "no": 2, "name": 'Mustafa Kemal’den Atatürk’e'},
        {"unit_id": 'turkce-1-tema-3-cevremizdeki-yasam', "grade": 1, "no": 3, "name": 'Çevremizdeki Yaşam'},
        {"unit_id": 'turkce-1-tema-4-yol-arkadasimiz-kitaplar', "grade": 1, "no": 4, "name": 'Yol Arkadaşımız Kitaplar'},
        {"unit_id": 'turkce-1-tema-5-yeteneklerimizi-kesfediyoruz', "grade": 1, "no": 5, "name": 'Yeteneklerimizi Keşfediyoruz'},
        {"unit_id": 'turkce-1-tema-6-minik-k-sifler', "grade": 1, "no": 6, "name": 'Minik Kâşifler'},
        {"unit_id": 'turkce-1-tema-7-atalarimizin-izleri', "grade": 1, "no": 7, "name": 'Atalarımızın İzleri'},
        {"unit_id": 'turkce-1-tema-8-sorumluluklarimizin-farkindayiz', "grade": 1, "no": 8, "name": 'Sorumluluklarımızın Farkındayız'},
    ],
    2: [
        {"unit_id": 'turkce-2-tema-1-degerlerimizle-variz', "grade": 2, "no": 1, "name": 'Değerlerimizle Varız'},
        {"unit_id": 'turkce-2-tema-2-ataturk-ve-cocuk', "grade": 2, "no": 2, "name": 'Atatürk Ve Çocuk'},
        {"unit_id": 'turkce-2-tema-3-dogada-neler-oluyor', "grade": 2, "no": 3, "name": 'Doğada Neler Oluyor?'},
        {"unit_id": 'turkce-2-tema-4-okuma-seruvenimiz', "grade": 2, "no": 4, "name": 'Okuma Serüvenimiz'},
        {"unit_id": 'turkce-2-tema-5-yeteneklerimizi-taniyoruz', "grade": 2, "no": 5, "name": 'Yeteneklerimizi Tanıyoruz'},
        {"unit_id": 'turkce-2-tema-6-mucit-cocuk', "grade": 2, "no": 6, "name": 'Mucit Çocuk'},
        {"unit_id": 'turkce-2-tema-7-kultur-hazinemiz', "grade": 2, "no": 7, "name": 'Kültür Hazinemiz'},
        {"unit_id": 'turkce-2-tema-8-haklarimizi-biliyoruz', "grade": 2, "no": 8, "name": 'Haklarımızı Biliyoruz'},
    ],
    3: [
        {"unit_id": 'turkce-3-tema-1-degerlerimizle-yasiyoruz', "grade": 3, "no": 1, "name": 'Değerlerimizle Yaşıyoruz'},
        {"unit_id": 'turkce-3-tema-2-ataturk-ve-kahramanlarimiz', "grade": 3, "no": 2, "name": 'Atatürk Ve Kahramanlarımız'},
        {"unit_id": 'turkce-3-tema-3-dogayi-taniyoruz', "grade": 3, "no": 3, "name": 'Doğayı Tanıyoruz'},
        {"unit_id": 'turkce-3-tema-4-bilgi-hazinemiz', "grade": 3, "no": 4, "name": 'Bilgi Hazinemiz'},
        {"unit_id": 'turkce-3-tema-5-yeteneklerimizi-kullaniyoruz', "grade": 3, "no": 5, "name": 'Yeteneklerimizi Kullanıyoruz'},
        {"unit_id": 'turkce-3-tema-6-bilim-yolculugu', "grade": 3, "no": 6, "name": 'Bilim Yolculuğu'},
        {"unit_id": 'turkce-3-tema-7-mill-kulturumuz', "grade": 3, "no": 7, "name": 'Millî Kültürümüz'},
        {"unit_id": 'turkce-3-tema-8-hak-ve-sorumluluklarimiz', "grade": 3, "no": 8, "name": 'Hak Ve Sorumluluklarımız'},
    ],
    4: [
        {"unit_id": 'turkce-4-tema-1-erdemler', "grade": 4, "no": 1, "name": 'Erdemler'},
        {"unit_id": 'turkce-4-tema-2-mill-mucadele-ve-ataturk', "grade": 4, "no": 2, "name": 'Millî Mücadele Ve Atatürk'},
        {"unit_id": 'turkce-4-tema-3-doga-ve-insan', "grade": 4, "no": 3, "name": 'Doğa Ve İnsan'},
        {"unit_id": 'turkce-4-tema-4-kutuphanemiz', "grade": 4, "no": 4, "name": 'Kütüphanemiz'},
        {"unit_id": 'turkce-4-tema-5-kendimizi-gelistiriyoruz', "grade": 4, "no": 5, "name": 'Kendimizi Geliştiriyoruz'},
        {"unit_id": 'turkce-4-tema-6-bilim-ve-teknoloji', "grade": 4, "no": 6, "name": 'Bilim Ve Teknoloji'},
        {"unit_id": 'turkce-4-tema-7-gecmisten-gelecege-mirasimiz', "grade": 4, "no": 7, "name": 'Geçmişten Geleceğe Mirasımız'},
        {"unit_id": 'turkce-4-tema-8-demokratik-yasam', "grade": 4, "no": 8, "name": 'Demokratik Yaşam'},
    ],
    5: [
        {"unit_id": 'turkce-5-tema-1-oyun-dunyasi', "grade": 5, "no": 1, "name": 'Oyun Dünyası'},
        {"unit_id": 'turkce-5-tema-2-ataturku-tanimak', "grade": 5, "no": 2, "name": 'Atatürk’ü Tanımak'},
        {"unit_id": 'turkce-5-tema-3-duygularimi-taniyorum', "grade": 5, "no": 3, "name": 'Duygularımı Tanıyorum'},
        {"unit_id": 'turkce-5-tema-4-geleneklerimiz', "grade": 5, "no": 4, "name": 'Geleneklerimiz'},
        {"unit_id": 'turkce-5-tema-5-iletisim-ve-sosyal-iliskiler', "grade": 5, "no": 5, "name": 'İletişim Ve Sosyal İlişkiler'},
        {"unit_id": 'turkce-5-tema-6-saglikli-yasiyorum', "grade": 5, "no": 6, "name": 'Sağlıklı Yaşıyorum'},
    ],
    6: [
        {"unit_id": 'turkce-6-tema-1-dilimizin-zenginligi', "grade": 6, "no": 1, "name": 'Dilimizin Zenginliği'},
        {"unit_id": 'turkce-6-tema-2-bagimsizlik-yolu', "grade": 6, "no": 2, "name": 'Bağımsızlık Yolu'},
        {"unit_id": 'turkce-6-tema-3-farkli-dunyalar', "grade": 6, "no": 3, "name": 'Farklı Dünyalar'},
        {"unit_id": 'turkce-6-tema-4-iletisim-ve-sosyal-iliskiler', "grade": 6, "no": 4, "name": 'İletişim Ve Sosyal İlişkiler'},
        {"unit_id": 'turkce-6-tema-5-bilim-ve-teknoloji', "grade": 6, "no": 5, "name": 'Bilim Ve Teknoloji'},
        {"unit_id": 'turkce-6-tema-6-lider-ruhlar', "grade": 6, "no": 6, "name": 'Lider Ruhlar'},
    ],
    7: [
        {"unit_id": 'turkce-7-tema-1-hayat-boyu-gelisim', "grade": 7, "no": 1, "name": 'Hayat Boyu Gelişim'},
        {"unit_id": 'turkce-7-tema-2-bir-hilal-ugruna', "grade": 7, "no": 2, "name": 'Bir Hilal Uğruna'},
        {"unit_id": 'turkce-7-tema-3-iletisim-ve-sosyal-iliskiler', "grade": 7, "no": 3, "name": 'İletişim Ve Sosyal İlişkiler'},
        {"unit_id": 'turkce-7-tema-4-turk-sanati', "grade": 7, "no": 4, "name": 'Türk Sanatı'},
        {"unit_id": 'turkce-7-tema-5-okuma-kulturu', "grade": 7, "no": 5, "name": 'Okuma Kültürü'},
        {"unit_id": 'turkce-7-tema-6-hak-ve-sorumluluklar', "grade": 7, "no": 6, "name": 'Hak Ve Sorumluluklar'},
    ],
    8: [
        {"unit_id": 'turkce-8-tema-1-iletisim-ve-sosyal-iliskiler', "grade": 8, "no": 1, "name": 'İletişim Ve Sosyal İlişkiler'},
        {"unit_id": 'turkce-8-tema-2-vatan-sevgisi', "grade": 8, "no": 2, "name": 'Vatan Sevgisi'},
        {"unit_id": 'turkce-8-tema-3-doga-ve-insan', "grade": 8, "no": 3, "name": 'Doğa Ve İnsan'},
        {"unit_id": 'turkce-8-tema-4-turk-hik-ye-gelenegi-ve-destanlari', "grade": 8, "no": 4, "name": 'Türk Hikâye Geleneği Ve Destanları'},
        {"unit_id": 'turkce-8-tema-5-sanat-ve-estetik', "grade": 8, "no": 5, "name": 'Sanat Ve Estetik'},
        {"unit_id": 'turkce-8-tema-6-akademik-dusunme-dunyasi', "grade": 8, "no": 6, "name": 'Akademik Düşünme Dünyası'},
    ],
}


def _with_kazanimlar(theme: dict) -> TrUnit:
    return {**theme, "kazanimlar": GRADE_KAZANIMLAR.get(theme["grade"], [])}  # type: ignore[return-value]


TURKCE_CURRICULUM: dict[int, list[TrUnit]] = {
    g: [_with_kazanimlar(t) for t in ts] for g, ts in _THEMES.items()
}


def get_units_for_grade(grade: int) -> list[TrUnit]:
    return list(TURKCE_CURRICULUM.get(grade, []))


def get_unit(grade: int, unit_id: str) -> TrUnit | None:
    for u in TURKCE_CURRICULUM.get(grade, []):
        if u["unit_id"] == unit_id:
            return u
    return None


def get_unit_kazanim(grade: int, unit_id: str, kazanim_kod: str) -> TrKazanim | None:
    for k in GRADE_KAZANIMLAR.get(grade, []):
        if k["kod"] == kazanim_kod:
            return k
    return None


def find_unit_by_kazanim(kazanim_kod: str) -> tuple[int, TrUnit] | None:
    # Kazanım sınıf-düzeyi (temaya bağlı değil) → sınıfın ilk teması döner.
    for grade, kzs in GRADE_KAZANIMLAR.items():
        if any(k["kod"] == kazanim_kod for k in kzs):
            units = get_units_for_grade(grade)
            if units:
                return grade, units[0]
    return None


def is_unit_available(grade: int, unit_id: str) -> bool:
    return get_unit(grade, unit_id) is not None
