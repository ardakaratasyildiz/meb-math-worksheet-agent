"""Fen Bilimleri müfredatı — 2024 TYMM, ÜNİTE BAZLI (otomatik üretildi).

Kaynak: knowledge_base/Fen/mufredat/fen_ogretim_programi_2024_TYMM.pdf
Üretici: scripts/derive_fen_curriculum.py (deterministik, LLM'siz).
Kod: FB.{sınıf}.{ünite}.{çıktı} (3-4. sınıf) / FB.{sınıf}.{ünite}.{bölüm}.{çıktı} (5-8).

difficulty_hints: app/subjects/fen/difficulty_hints.py'den gömülür (elle
yazıldı; generator yeniden koşarsa korunur). İlk pass — Faz 6'da rafine edilir.
"""
from __future__ import annotations

from typing import NotRequired, TypedDict


class FenKazanim(TypedDict):
    kod: str
    metin: str
    difficulty_hints: NotRequired[dict[str, str]]


class FenUnit(TypedDict):
    unit_id: str          # kararlı slug, örn. 'fen-5-unite-1-gokyuzundeki-komsularimiz-ve-biz'
    grade: int
    no: int               # ünite sırası
    name: str
    kazanimlar: list[FenKazanim]


FEN_CURRICULUM: dict[int, list[FenUnit]] = {
    3: [
        {
            "unit_id": 'fen-3-unite-1-bilimsel-kesif-yolculugu',
            "grade": 3,
            "no": 1,
            "name": 'Bilimsel Keşif Yolculuğu',
            "kazanimlar": [
                {
                    "kod": 'FB.3.1.1',
                    "metin": 'Bilimsel bilgiye ulaşma yollarını sorgulayabilme',
                    "difficulty_hints": {
                        "kolay": 'Bilgiye ulaşma yollarından birini (kitap, gözlem, deney, internet) tanıma; tek bir kaynağı seçme.',
                        "orta": 'Belirli bir soruya doğru bilgi kaynağını eşleştirme; iki farklı ulaşma yolunu kısa örnekle ayırt etme.',
                        "zor": 'Bir günlük durumda hangi yolun daha güvenilir bilgi vereceğini gerekçelendirerek seçip nedenini açıklama.',
                    },
                },
                {
                    "kod": 'FB.3.1.2',
                    "metin": 'Bilim insanlarının özelliklerine ilişkin genelleme yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir bilim insanının bilinen bir özelliğini (meraklı, gözlemci, sabırlı) doğrudan tanıma veya eşleştirme.',
                        "orta": 'Verilen kısa davranış örneğinden bilim insanına ait özelliği çıkarma; iki özelliği örnekle ilişkilendirme.',
                        "zor": 'Kısa bir hikâyedeki davranışları değerlendirip hangi kişinin bilim insanı gibi çalıştığını gerekçeyle belirleme.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-3-unite-2-canlilar-dunyasina-yolculuk',
            "grade": 3,
            "no": 2,
            "name": 'Canlılar Dünyasına Yolculuk',
            "kazanimlar": [
                {
                    "kod": 'FB.3.2.1',
                    "metin": 'Canlıları; mikroskopla görülebilen canlılar, mantarlar, bitkiler ve hayvanlar olarak sınıflandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Verilen tek bir canlıyı (bitki, hayvan, mantar) doğru gruba yerleştirme; tanıdık örnek.',
                        "orta": 'Birkaç canlıyı özelliklerine bakarak bitki/hayvan/mantar gruplarına ayırma; görsel destekli sınıflandırma.',
                        "zor": 'Karışık canlı listesini mikroskobik/mantar/bitki/hayvan olarak ayırıp ayırt edici özelliği açıklama; çeldirici içerir.',
                    },
                },
                {
                    "kod": 'FB.3.2.2',
                    "metin": 'Canlıların çevrelerini farklı yollarla algılamaları konusunda bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir duyu organını (göz, kulak, burun) ve ne işe yaradığını doğrudan tanıma; tek eşleştirme.',
                        "orta": 'Verilen durumda hayvanın çevresini hangi duyuyla algıladığını basit gözlemden çıkarma.',
                        "zor": 'Bir senaryoda canlının farklı algılama yollarını karşılaştırıp neden o yolu kullandığını çıkarımla açıklama.',
                    },
                },
                {
                    "kod": 'FB.3.2.3',
                    "metin": 'Canlıların yaşam döngülerini açıklamada tümevarımsal akıl yürütebilme',
                    "difficulty_hints": {
                        "kolay": 'Bir canlının yaşam döngüsündeki tek bir aşamayı (yumurta, yavru) tanıma veya adlandırma.',
                        "orta": 'Kelebek veya tavuk gibi bir canlının döngü aşamalarını doğru sıraya koyma; görsel destekli.',
                        "zor": 'Farklı canlıların döngülerini karşılaştırıp ortak örüntüden genel bir sonuç çıkararak açıklama.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-3-unite-3-yer-bilimciler-is-basinda',
            "grade": 3,
            "no": 3,
            "name": 'Yer Bilimciler İş Başında',
            "kazanimlar": [
                {
                    "kod": 'FB.3.3.1',
                    "metin": 'Kayaçlar, madenler ve mineraller ile ilgili tümdengelimsel akıl yürütebilme',
                    "difficulty_hints": {
                        "kolay": 'Kayaç, maden veya minerali örnekle tanıma; bir özelliğini (sertlik, renk) doğrudan belirtme.',
                        "orta": 'Verilen özelliklerden hangi taşın hangi gruba girdiğini çıkarma; iki örneği karşılaştırma.',
                        "zor": 'Genel bir kurala dayanarak bilinmeyen bir örneğin türünü tümdengelimle belirleyip gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.3.3.2',
                    "metin": 'Fosil oluşumu ile ilgili sentez yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Fosilin ne olduğunu tanıma; bir fosil örneğini basit görselden seçme.',
                        "orta": 'Fosil oluşumundaki aşamaları sıralama; hangi ortamda fosil oluştuğunu basit veriden çıkarma.',
                        "zor": 'Fosil ipuçlarından geçmiş bir canlı veya ortam hakkında sentezle mantıklı bir tahmin oluşturup açıklama.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-3-unite-4-maddeyi-taniyalim-karistirip-ayiralim',
            "grade": 3,
            "no": 4,
            "name": 'Maddeyi Tanıyalım, Karıştırıp Ayıralım',
            "kazanimlar": [
                {
                    "kod": 'FB.3.4.1',
                    "metin": 'Çevresindeki maddeleri hâllerine göre sınıflandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir maddenin hâlini (katı, sıvı, gaz) tanıdık örnekle doğrudan belirleme.',
                        "orta": 'Verilen birkaç maddeyi hâllerine göre gruplama; görsel veya kısa açıklamadan çıkarım yapma.',
                        "zor": 'Karışık madde listesini hâllerine göre sınıflandırıp ayırt edici özelliği gerekçeyle açıklama; çeldirici içerir.',
                    },
                },
                {
                    "kod": 'FB.3.4.2',
                    "metin": 'Günlük yaşamda karşılaştığı karışımların ayrılmasında kullanılabilecek uygun yöntemleri kullanarak deney yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Basit bir ayırma yöntemini (eleme, süzme, mıknatısla ayırma) tanıma; araç-yöntem eşleştirme.',
                        "orta": 'Verilen karışım için uygun ayırma yöntemini seçme; deney adımını kısa gözlemden çıkarma.',
                        "zor": 'Birden çok bileşenli karışım için doğru ayırma sırasını planlayıp neden o yöntemi seçtiğini açıklama.',
                    },
                },
                {
                    "kod": 'FB.3.4.3',
                    "metin": 'Atıkların ayrıştırılmasına ilişkin problem çözebilme',
                    "difficulty_hints": {
                        "kolay": 'Bir atığı doğru geri dönüşüm kutusuna (kâğıt, plastik, cam) eşleştirme; tek örnek.',
                        "orta": 'Karışık atıkları türlerine göre ayırma; hangi atığın nereye gideceğini kısa bağlamdan çıkarma.',
                        "zor": 'Gerçekçi bir atık ayrıştırma probleminde çözüm önerip neden ayrıştırmanın yararlı olduğunu gerekçelendirme.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-3-unite-5-hareketi-kesfediyorum',
            "grade": 3,
            "no": 5,
            "name": 'Hareketi Keşfediyorum',
            "kazanimlar": [
                {
                    "kod": 'FB.3.5.1',
                    "metin": 'Varlıkların hareket durumlarını gözleme dayalı tahmin edebilme',
                    "difficulty_hints": {
                        "kolay": 'Bir varlığın hareket edip etmediğini görselden tanıma; hareketli/durgun ayrımı yapma.',
                        "orta": 'Verilen bir durumda varlığın nasıl hareket edeceğini (hızlanma, durma) gözleme dayalı tahmin etme.',
                        "zor": 'Farklı hareket örneklerini karşılaştırıp bir sonraki durumu neden-sonuçla muhakeme ederek tahmin etme.',
                    },
                },
                {
                    "kod": 'FB.3.5.2',
                    "metin": 'Kuvvetin varlıklar üzerindeki etkilerini bilimsel gözleme dayalı tahmin edebilme',
                    "difficulty_hints": {
                        "kolay": 'Kuvvetin bir etkisini (itme, çekme, şekil değiştirme) tanıdık örnekle doğrudan tanıma.',
                        "orta": 'Verilen durumda kuvvetin cisme ne yapacağını (hareket, durdurma, biçim) gözleme dayalı tahmin etme.',
                        "zor": 'Bir senaryoda uygulanan kuvvetin birden çok etkisini muhakeme edip sonucu gerekçeyle tahmin etme.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-3-unite-6-yasamimizi-kolaylastiran-elektrik',
            "grade": 3,
            "no": 6,
            "name": 'Yaşamımızı Kolaylaştıran Elektrik',
            "kazanimlar": [
                {
                    "kod": 'FB.3.6.1',
                    "metin": 'Bazı araç gereçlerin elektrikli olduğuna ilişkin bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir aracın elektrikle çalışıp çalışmadığını tanıdık örnekle doğrudan belirleme.',
                        "orta": 'Verilen araçları elektrikli ve elektriksiz olarak gruplama; ipuçlarından çıkarım yapma.',
                        "zor": 'Bir aracın neden elektrikli olduğunu belirtilerden çıkarımla belirleyip gerekçesini açıklama; çeldirici içerir.',
                    },
                },
                {
                    "kod": 'FB.3.6.2',
                    "metin": 'Elektrikli araç gereçlerin güvenli kullanımı ile ilgili eleştirel düşünebilme',
                    "difficulty_hints": {
                        "kolay": 'Elektrikli araçla ilgili tek bir güvenlik kuralını (ıslak elle dokunma) tanıma.',
                        "orta": 'Verilen bir davranışın güvenli mi tehlikeli mi olduğunu kısa bağlamdan değerlendirip ayırt etme.',
                        "zor": 'Bir günlük sahnedeki tehlikeli kullanımı eleştirip nedenini ve doğru davranışı gerekçeyle açıklama.',
                    },
                },
                {
                    "kod": 'FB.3.6.3',
                    "metin": 'Elektriği tasarruflu kullanma konusunda bilimsel veriye dayalı tahmin edebilme',
                    "difficulty_hints": {
                        "kolay": 'Elektrik tasarrufu için tek bir davranışı (ışığı kapatma) tanıma veya seçme.',
                        "orta": 'Verilen basit veriden hangi davranışın tasarruf sağladığını çıkarma; iki durumu karşılaştırma.',
                        "zor": 'Bir evin kullanım verisine dayanarak tasarruf için öneri geliştirip neden işe yarayacağını tahminle açıklama.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-3-unite-7-topragi-taniyorum-tarimi-kesfediyorum',
            "grade": 3,
            "no": 7,
            "name": 'Toprağı Tanıyorum, Tarımı Keşfediyorum',
            "kazanimlar": [
                {
                    "kod": 'FB.3.7.1',
                    "metin": 'Toprak oluşumuna ve yapısına ilişkin bilimsel gözlem yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Toprağın gözlenebilen bir özelliğini (renk, tanecik, nem) doğrudan tanıma veya adlandırma.',
                        "orta": 'Verilen iki toprak örneğini gözlem özelliklerine göre karşılaştırıp farkı belirtme.',
                        "zor": 'Toprak katmanlarını veya oluşum ipuçlarını gözleme dayanarak çözümleyip nasıl oluştuğunu açıklama.',
                    },
                },
                {
                    "kod": 'FB.3.7.2',
                    "metin": 'Bir bitkinin yetişmesi için gerekenlere ilişkin genelleme yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir bitkinin yetişmesi için gereken tek bir öğeyi (su, ışık, toprak) tanıma.',
                        "orta": 'Verilen basit deney/gözlemden bitkinin neye ihtiyaç duyduğunu çıkarma; iki koşulu karşılaştırma.',
                        "zor": 'Farklı koşullardaki bitki sonuçlarını inceleyip yetişme için gerekenler hakkında genel kural çıkarma.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-3-unite-8-canlilarin-yasam-alanlarina-yolculuk',
            "grade": 3,
            "no": 8,
            "name": 'Canlıların Yaşam Alanlarına Yolculuk',
            "kazanimlar": [
                {
                    "kod": 'FB.3.8.1',
                    "metin": 'Canlıların yaşam alanlarının özelliklerini belirlemeye yönelik kanıt kullanabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir yaşam alanının (orman, göl, çöl) tek bir özelliğini doğrudan tanıma veya eşleştirme.',
                        "orta": 'Verilen ipuçlarından hangi yaşam alanının anlatıldığını kanıtla belirleme; iki alanı karşılaştırma.',
                        "zor": 'Bir canlının hangi yaşam alanına ait olduğunu birden çok kanıtı değerlendirerek gerekçeyle belirleme.',
                    },
                },
                {
                    "kod": 'FB.3.8.2',
                    "metin": 'Yaşam alanındaki canlı çeşitliliğini operasyonel olarak tanımlayabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir yaşam alanındaki tek bir canlıyı tanıma; canlı çeşitliliği kavramını basitçe belirtme.',
                        "orta": 'Verilen görsel veya listeden bir alandaki farklı canlıları sayıp çeşitliliği tanımlama.',
                        "zor": 'İki yaşam alanının canlı çeşitliliğini karşılaştırıp hangisinin daha zengin olduğunu gerekçeyle açıklama.',
                    },
                },
                {
                    "kod": 'FB.3.8.3',
                    "metin": 'Yaşam alanlarının korunması için yapılacakları sorgulayabilme',
                    "difficulty_hints": {
                        "kolay": 'Yaşam alanını korumak için tek bir davranışı (çöp atmama, ağaç dikme) tanıma.',
                        "orta": 'Verilen bir tehdide karşı hangi koruma davranışının uygun olduğunu kısa bağlamdan seçme.',
                        "zor": 'Bir yaşam alanı tehdidini sorgulayıp koruma için öneri geliştirerek neden gerekli olduğunu açıklama.',
                    },
                },
            ],
        },
    ],
    4: [
        {
            "unit_id": 'fen-4-unite-1-bilime-yolculuk',
            "grade": 4,
            "no": 1,
            "name": 'Bilime Yolculuk',
            "kazanimlar": [
                {
                    "kod": 'FB.4.1.1',
                    "metin": 'Bilimin özellikleri ile ilgili yansıtma yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Bilimin temel bir özelliğini (gözleme dayanma, kanıt arama) doğrudan hatırlama; tek doğru tanım.',
                        "orta": 'Verilen kısa bir bilimsel çalışma örneğinde hangi özelliğin kullanıldığını ilişkilendirme; günlük bağlam.',
                        "zor": 'İki farklı örneği karşılaştırıp hangisinin bilimin özelliklerine daha uygun olduğunu gerekçesiyle değerlendirme.',
                    },
                },
                {
                    "kod": 'FB.4.1.2',
                    "metin": 'Bilgi kaynağının güvenilirliğini sorgulayabilme',
                    "difficulty_hints": {
                        "kolay": 'Güvenilir bir bilgi kaynağını (ansiklopedi, uzman) güvenilmezden doğrudan ayırt etme; tanıma düzeyi.',
                        "orta": 'Verilen iki kaynağı karşılaştırıp hangisinin daha güvenilir olduğunu basit ölçütle seçme; kısa senaryo.',
                        "zor": 'Çelişen bilgiler içeren birkaç kaynağı sorgulayıp hangisine neden güvenileceğini gerekçelendirerek değerlendirme.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-4-unite-2-saglikli-besleniyorum',
            "grade": 4,
            "no": 2,
            "name": 'Sağlıklı Besleniyorum',
            "kazanimlar": [
                {
                    "kod": 'FB.4.2.1',
                    "metin": 'Besin içeriklerini ayırt etmek için deney yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir besin içeriğini belirleyen basit testi (nişasta-iyot) doğrudan hatırlama; tek adımlı tanıma.',
                        "orta": 'Verilen deney sonucundaki renk/iz değişiminden besinde hangi içeriğin bulunduğuna çıkarım yapma.',
                        "zor": 'Birkaç besinin deney sonuçlarını karşılaştırıp içeriklerini ayırt ederek tabloyu yorumlama; çeldiricili muhakeme.',
                    },
                },
                {
                    "kod": 'FB.4.2.2',
                    "metin": 'Besinlerde vitamin ve/veya mineral bulunduğuna ilişkin genelleme yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir besinin vitamin veya mineral kaynağı olduğunu doğrudan eşleştirme (portakal-C vitamini); hatırlama.',
                        "orta": 'Verilen birkaç besin örneğinden ortak bir sonuca (hepsi mineral içerir) ulaşma; basit genelleme.',
                        "zor": 'Farklı besin gruplarındaki verilerden vitamin/mineral genellemesi kurup istisnayı ayırt ederek gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.4.2.3',
                    "metin": 'Besinlerin işlevleri ile ilgili hipotez oluşturabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir besin grubunun temel işlevini (enerji verir, büyütür) doğrudan hatırlama; tek eşleşme.',
                        "orta": 'Verilen beslenme durumundan besinin işleviyle ilgili basit bir tahmin/hipotez kurma; günlük bağlam.',
                        "zor": 'Eksik besin senaryosunda olası sonucu işlevlerle ilişkilendirerek hipotez kurma ve gerekçelendirme.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-4-unite-3-dunyamizi-kesfedelim',
            "grade": 4,
            "no": 3,
            "name": "Dünya'mızı Keşfedelim",
            "kazanimlar": [
                {
                    "kod": 'FB.4.3.1',
                    "metin": 'Dünya’nın şekli ile ilgili bilimsel gözleme dayalı tahmin yapabilme',
                    "difficulty_hints": {
                        "kolay": "Dünya'nın küre (yuvarlak) şeklini doğrudan tanıma; tek görsel veya bilgi hatırlama.",
                        "orta": "Gemi ufukta kaybolması gibi bir gözlemden Dünya'nın şekline ilişkin basit tahmin yapma.",
                        "zor": 'Birkaç gözlemi (ufuk, gölge, uzay görüntüsü) birlikte değerlendirip şekil tahminini gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.4.3.2',
                    "metin": 'Dünya’nın yapısıyla ilgili bilimsel model oluşturabilme',
                    "difficulty_hints": {
                        "kolay": "Dünya'nın katmanlarını (kabuk, iç kısımlar) doğrudan sıralama veya tanıma; hatırlama düzeyi.",
                        "orta": 'Verilen model/kesitte katmanları eşleştirip sıralarını yorumlama; basit görsel analiz.',
                        "zor": 'Katmanların özelliklerini karşılaştırıp bir model kurmanın neden uygun olduğunu değerlendirme; çeldiricili.',
                    },
                },
                {
                    "kod": 'FB.4.3.3',
                    "metin": 'Dünya’nın hareketlerini gözlemlerine dayanarak tahmin edebilme',
                    "difficulty_hints": {
                        "kolay": "Dünya'nın dönme veya dolanma hareketini doğrudan tanıma; tek kavram hatırlama.",
                        "orta": "Gece-gündüz oluşumunu Dünya'nın dönmesiyle ilişkilendirerek basit tahmin yapma; günlük gözlem.",
                        "zor": 'Dönme ve dolanma hareketlerini karşılaştırıp hangi olayın (mevsim, gece-gündüz) hangisinden kaynaklandığını gerekçelendirme.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-4-unite-4-maddenin-degisimi',
            "grade": 4,
            "no": 4,
            "name": 'Maddenin Değişimi',
            "kazanimlar": [
                {
                    "kod": 'FB.4.4.1',
                    "metin": 'Maddelerin hâl değişimine yönelik bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir hâl değişimini (erime, donma) doğrudan tanıma veya adlandırma; tek örnek hatırlama.',
                        "orta": 'Verilen günlük olayda (buz erimesi) gerçekleşen hâl değişimini çıkarımla belirleme; kısa bağlam.',
                        "zor": 'Birden çok hâl değişiminin sıralı olduğu senaryoyu çözümleyip her aşamayı gerekçesiyle çıkarımlama.',
                    },
                },
                {
                    "kod": 'FB.4.4.2',
                    "metin": 'Maddelerin ısı etkisiyle değişimine yönelik deney yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Isının maddeyi eritme/buharlaştırma etkisini doğrudan hatırlama; tek adımlı tanıma.',
                        "orta": 'Verilen ısıtma deneyi sonucundan maddede oluşan değişime çıkarım yapma; basit gözlem yorumu.',
                        "zor": 'Farklı maddelerin ısıya tepkisini karşılaştıran deney tasarımını değerlendirip sonucu gerekçelendirme.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-4-unite-5-miknatisi-kesfediyorum',
            "grade": 4,
            "no": 5,
            "name": 'Mıknatısı Keşfediyorum',
            "kazanimlar": [
                {
                    "kod": 'FB.4.5.1',
                    "metin": 'Mıknatısın kutupları ve birbirleriyle etkileşimleri ile ilgili tümevarımsal akıl yürütebilme',
                    "difficulty_hints": {
                        "kolay": 'Mıknatısın iki kutbu (N-S) olduğunu doğrudan hatırlama; tek bilgi tanıma.',
                        "orta": 'Verilen iki mıknatıs konumunda çekme mi itme mi olacağını kutuplardan çıkarım yapma.',
                        "zor": "Birden çok kutup etkileşimi örneğinden 'zıt çeker, aynı iter' kuralını tümevarımla çıkarıp gerekçelendirme.",
                    },
                },
                {
                    "kod": 'FB.4.5.2',
                    "metin": 'Mıknatısın etki ettiği maddelere ilişkin bilimsel gözleme dayalı tahmin yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Mıknatısın demiri çektiğini, tahtayı çekmediğini doğrudan tanıma; tek örnek hatırlama.',
                        "orta": 'Verilen nesne listesinden mıknatısın hangilerini çekeceğine ilişkin gözleme dayalı tahmin yapma.',
                        "zor": 'Karışık maddelerden mıknatısla ayırma senaryosunu çözümleyip hangilerinin ayrılacağını gerekçesiyle tahmin etme.',
                    },
                },
                {
                    "kod": 'FB.4.5.3',
                    "metin": 'Mıknatısın kullanım alanlarına yönelik bilimsel sorgulama yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Mıknatısın bir kullanım alanını (pusula, buzdolabı süsü) doğrudan hatırlama; tek eşleşme.',
                        "orta": 'Verilen günlük araçta mıknatısın neden kullanıldığını sorgulayıp işleviyle ilişkilendirme.',
                        "zor": 'Bir soruna mıknatıs kullanan çözüm önerip bunun neden uygun olduğunu değerlendirme; gerçekçi senaryo.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-4-unite-6-enerji-dedektifleri',
            "grade": 4,
            "no": 6,
            "name": 'Enerji Dedektifleri',
            "kazanimlar": [
                {
                    "kod": 'FB.4.6.1',
                    "metin": 'Basit bir elektrik devresi kurmaya ilişkin bilimsel sorgulama yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Basit devrenin temel parçalarını (pil, ampul, kablo) doğrudan tanıma; hatırlama düzeyi.',
                        "orta": 'Verilen devre şemasında ampulün yanıp yanmayacağını bağlantılardan çıkarımla belirleme.',
                        "zor": 'Çalışmayan bir devrenin nedenini sorgulayıp eksik/hatalı bağlantıyı belirleyerek çözüm önerme.',
                    },
                },
                {
                    "kod": 'FB.4.6.2',
                    "metin": 'Elektrik üretiminde yenilenebilir ve yenilenemeyen enerji kaynaklarını kullanmaya ilişkin eleştirel düşünebilme',
                    "difficulty_hints": {
                        "kolay": 'Yenilenebilir (güneş, rüzgâr) ve yenilenemeyen (kömür) kaynağı doğrudan ayırt etme; tanıma.',
                        "orta": 'Verilen enerji kaynağının yenilenebilir olup olmadığını özelliğinden çıkarımla sınıflandırma.',
                        "zor": 'İki enerji kaynağının çevresel etkilerini karşılaştırıp hangisinin tercih edilmesi gerektiğini eleştirel gerekçelendirme.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-4-unite-7-isigin-pesinde',
            "grade": 4,
            "no": 7,
            "name": 'Işığın Peşinde',
            "kazanimlar": [
                {
                    "kod": 'FB.4.7.1',
                    "metin": 'Görme olayının gerçekleşebilmesi için ışığın rolüne ilişkin deney yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Görmek için ışığa ihtiyaç olduğunu doğrudan hatırlama; tek kavram tanıma.',
                        "orta": 'Karanlık oda deneyinden cismin neden görünmediğine ışığın rolüyle çıkarım yapma; kısa bağlam.',
                        "zor": 'Işık kaynağı-cisim-göz ilişkisini çözümleyip görmenin hangi koşulda gerçekleştiğini gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.4.7.2',
                    "metin": 'Doğal ve yapay ışık kaynaklarını karşılaştırabilme',
                    "difficulty_hints": {
                        "kolay": 'Doğal (Güneş) ve yapay (ampul) ışık kaynağını doğrudan ayırt etme; tek eşleşme hatırlama.',
                        "orta": 'Verilen ışık kaynaklarını doğal-yapay olarak sınıflandırıp özelliklerini karşılaştırma; basit analiz.',
                        "zor": 'Doğal ve yapay kaynakları çeşitli ölçütlerle karşılaştırıp bir durumda hangisinin uygun olduğunu değerlendirme.',
                    },
                },
                {
                    "kod": 'FB.4.7.3',
                    "metin": 'Işık kirliliğinin canlılara etkisine ilişkin probleme yönelik çözüm önerilerini değerlendirebilme',
                    "difficulty_hints": {
                        "kolay": 'Işık kirliliğinin bir olumsuz etkisini doğrudan hatırlama; tek bilgi tanıma.',
                        "orta": 'Verilen aşırı aydınlatma örneğinin canlılara etkisini çıkarımla ilişkilendirme; günlük bağlam.',
                        "zor": 'Işık kirliliği sorununa sunulan çözüm önerilerini karşılaştırıp en uygununu gerekçesiyle değerlendirme.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-4-unite-8-surdurulebilir-sehirler-ve-topluluklar',
            "grade": 4,
            "no": 8,
            "name": 'Sürdürülebilir Şehirler ve Topluluklar',
            "kazanimlar": [
                {
                    "kod": 'FB.4.8.1',
                    "metin": 'Sürdürülebilir bir yaşam alanı kurmaya ilişkin bilimsel sorgulama yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Sürdürülebilir yaşam alanının bir özelliğini (geri dönüşüm, yeşil alan) doğrudan tanıma; hatırlama.',
                        "orta": 'Verilen şehir örneğinde hangi uygulamanın sürdürülebilirliği artırdığını sorgulayıp belirleme.',
                        "zor": 'Bir yaşam alanı için sürdürülebilir çözümler önerip bunların çevreye etkisini değerlendirme; gerçekçi senaryo.',
                    },
                },
            ],
        },
    ],
    5: [
        {
            "unit_id": 'fen-5-unite-1-gokyuzundeki-komsularimiz-ve-biz',
            "grade": 5,
            "no": 1,
            "name": 'Gökyüzündeki Komşularımız ve Biz',
            "kazanimlar": [
                {
                    "kod": 'FB.5.1.1.1',
                    "metin": 'Güneş’in yapısı ve dönme hareketi ile ilgili bilgileri kaydedebilme',
                    "difficulty_hints": {
                        "kolay": "Güneş'in bir yıldız olduğunu veya kendi ekseninde döndüğünü doğrudan hatırlama; tek bilgi.",
                        "orta": "Güneş'in katman/yapı bilgisini dönme hareketiyle ilişkilendirme; verilen basit görselden doğru bilgiyi seçme.",
                        "zor": "Güneş'in yapısı ve dönmesine dair birden çok bilgiyi kaydeden bir tabloyu yorumlama; yanlış kaydı gerekçeyle ayıklama.",
                    },
                },
                {
                    "kod": 'FB.5.1.2.1',
                    "metin": 'Ay’ın özellikleri, dönme ve dolanma hareketleri ile ilgili bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": "Ay'ın Dünya'nın uydusu olduğunu veya kendi ışığı olmadığını hatırlama; tek adım tanıma.",
                        "orta": "Ay'ın dönme ve dolanma sürelerinin eşitliğinden hep aynı yüzü görmemizi ilişkilendirme; basit gözleme dayalı çıkarım.",
                        "zor": "Ay'ın hareketlerine ilişkin gözlem verisinden bilimsel çıkarım yapıp benzer görünen çeldirici açıklamaları değerlendirme.",
                    },
                },
                {
                    "kod": 'FB.5.1.2.2',
                    "metin": 'Ay’ın evrelerini temsil eden bilimsel model oluşturabilme',
                    "difficulty_hints": {
                        "kolay": 'Verilen bir Ay evresini (dolunay, yeni ay) adıyla eşleştirme; tek görsel tanıma.',
                        "orta": 'Işık kaynağı-Ay-gözlemci konumundan bir evrenin nasıl oluştuğunu temsil eden basit modeli açıklama.',
                        "zor": 'Evre sırasını modelle kurup Güneş-Dünya-Ay konumlarıyla neden o evrenin görüldüğünü çok adımlı gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.5.1.3.1',
                    "metin": 'Güneş, Dünya ve Ay’ın birbirlerine göre hareketlerini ve hacimsel büyüklüklerini temsil eden bilimsel model oluşturabilme',
                    "difficulty_hints": {
                        "kolay": "Güneş, Dünya, Ay'ı büyükten küçüğe hacimce sıralama; doğrudan bilgi.",
                        "orta": 'Üç gök cisminin göreli büyüklük ve konumunu gösteren basit modeli verilen ölçeğe göre yorumlama.',
                        "zor": 'Hacim oranlarını ve göreli hareketleri birlikte temsil eden bir modeli değerlendirip ölçek hatasını gerekçeyle bulma.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-5-unite-2-kuvveti-taniyalim',
            "grade": 5,
            "no": 2,
            "name": 'Kuvveti Tanıyalım',
            "kazanimlar": [
                {
                    "kod": 'FB.5.2.1.1',
                    "metin": 'Kuvveti büyüklüğü ile tanımlayabilme',
                    "difficulty_hints": {
                        "kolay": 'Kuvvetin itme ya da çekme olduğunu, biriminin Newton olduğunu hatırlama; tek adım.',
                        "orta": 'Verilen bir örnekte uygulanan kuvvetin büyüklüğünü/etkisini (şekil değiştirme, hareket) ilişkilendirme.',
                        "zor": 'Farklı büyüklükteki kuvvetlerin cisim üzerindeki etkilerini karşılaştıran senaryoyu çok adımlı değerlendirme.',
                    },
                },
                {
                    "kod": 'FB.5.2.1.2',
                    "metin": 'Basit araç gereçler kullanarak bir dinamometre modeli tasarlayabilme',
                    "difficulty_hints": {
                        "kolay": 'Dinamometrenin kuvvet ölçtüğünü ve yaylı olduğunu hatırlama; temel parça tanıma.',
                        "orta": 'Verilen yay ve malzemelerle basit dinamometre kurulumunun çalışma mantığını (yay uzaması) açıklama.',
                        "zor": 'Model dinamometrede yay seçimi, ölçek işaretleme ve kalibrasyonu içeren tasarımı adım adım gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.5.2.2.1',
                    "metin": 'Kütleye etki eden yer çekimi kuvvetini ağırlık olarak tanımlayabilme',
                    "difficulty_hints": {
                        "kolay": 'Ağırlığın yer çekimi kuvveti olduğunu ve Newton ile ölçüldüğünü hatırlama; tek bilgi.',
                        "orta": 'Kütle ile ağırlık kavramlarını verilen örnekte ayırt edip yer çekimiyle ilişkilendirme.',
                        "zor": 'Farklı gök cisimlerinde kütle sabit-ağırlık değişken senaryosunu neden-sonuçla çok adımlı değerlendirme.',
                    },
                },
                {
                    "kod": 'FB.5.2.3.1',
                    "metin": 'Sürtünme kuvvetinin çeşitli ortamlardaki etkilerine yönelik tümevarımsal akıl yürütebilme',
                    "difficulty_hints": {
                        "kolay": 'Sürtünmenin hareketi zorlaştırdığını veya yüzeye bağlı olduğunu hatırlama; tek adım.',
                        "orta": 'Farklı yüzeylerde kayan cismin gözlemini kullanarak sürtünme-yüzey pürüzü ilişkisini çıkarma.',
                        "zor": 'Birden çok ortam gözlemini karşılaştırıp tümevarımla genel kural oluşturma; aykırı sonucu gerekçeyle yorumlama.',
                    },
                },
                {
                    "kod": 'FB.5.2.3.2',
                    "metin": 'Günlük yaşamda sürtünmeyi artırma veya azaltmaya yönelik bilimsel bir model tasarlayabilme',
                    "difficulty_hints": {
                        "kolay": 'Günlükte sürtünmeyi artıran/azaltan bir örnek (kaymak için buz, tutmak için tırtıklı) seçme.',
                        "orta": 'Verilen bir sorunda sürtünmeyi artırma ya da azaltma çözümünü uygun malzemeyle eşleştirerek önerme.',
                        "zor": 'Gerçekçi bir problemde sürtünmeyi kontrol eden modeli tasarlayıp seçimleri neden-sonuçla değerlendirme.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-5-unite-3-canlilarin-yapisina-yolculuk',
            "grade": 5,
            "no": 3,
            "name": 'Canlıların Yapısına Yolculuk',
            "kazanimlar": [
                {
                    "kod": 'FB.5.3.1.1',
                    "metin": 'Bitki ve hayvan hücrelerini temel kısımları ve özellikleri açısından karşılaştırabilme',
                    "difficulty_hints": {
                        "kolay": 'Bitki hücresinde hücre duvarı veya kloroplast bulunduğunu hatırlama; tek yapı tanıma.',
                        "orta": 'Bitki ve hayvan hücresini verilen görselde ortak ve farklı kısımlar açısından karşılaştırma.',
                        "zor": 'İki hücre tipinin yapı-işlev farklarını tabloda çözümleyip yanlış eşleştirmeyi gerekçeyle düzeltme.',
                    },
                },
                {
                    "kod": 'FB.5.3.1.2',
                    "metin": 'Hücre-doku-organ-sistem-organizma kavramlarını yapılandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Hücre-doku-organ-sistem-organizma sıralamasında bir basamağı doğru yerleştirme; tek adım.',
                        "orta": 'Verilen bir örneği (kalp, kas) doğru organizasyon düzeyiyle eşleştirerek kavramları ilişkilendirme.',
                        "zor": 'Karışık verilen yapıları küçükten büyüğe organizasyon basamağına dizip mantığını çok adımlı gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.5.3.2.1',
                    "metin": 'Destek ve hareket sistemine ait yapıları sınıflandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Kemik, kas veya eklemi destek-hareket sistemi yapısı olarak tanıma; tek adım.',
                        "orta": 'Verilen yapıları kemik/kas/eklem gruplarına göre sınıflandırıp görevle basitçe ilişkilendirme.',
                        "zor": 'Farklı yapıları işlevlerine göre çok kritere göre sınıflandırıp yanlış gruplananı gerekçeyle ayıklama.',
                    },
                },
                {
                    "kod": 'FB.5.3.2.2',
                    "metin": 'Destek ve hareket sisteminin sağlığı için yapılması gerekenler konusunda bilgi toplayabilme',
                    "difficulty_hints": {
                        "kolay": 'Duruş bozukluğunu önleyen bir davranışı (doğru oturma) hatırlama; tek öneri.',
                        "orta": 'Verilen bir günlük durumun destek-hareket sağlığına etkisini kısa gerekçeyle değerlendirme.',
                        "zor": 'Toplanan bilgilerden sağlıklı yaşam önerileri oluşturup yanlış inanışı kanıtla çürütme; çok adımlı değerlendirme.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-5-unite-4-isigin-dunyasi',
            "grade": 5,
            "no": 4,
            "name": 'Işığın Dünyası',
            "kazanimlar": [
                {
                    "kod": 'FB.5.4.1.1',
                    "metin": 'Bir kaynaktan çıkan ışığın her yönde doğrusal bir yol izlediğini gözlem yoluyla açıklayabilme',
                    "difficulty_hints": {
                        "kolay": 'Işığın doğrusal yol izlediğini hatırlama; tek bilgi tanıma.',
                        "orta": 'Karton delik-fener düzeneği gözleminden ışığın doğrusal yayıldığını çıkarma; basit görsel yorum.',
                        "zor": 'Işığın doğrusallığını gölge/hizalama gözlemleriyle çok adımlı gerekçelendirip aykırı iddiayı değerlendirme.',
                    },
                },
                {
                    "kod": 'FB.5.4.2.1',
                    "metin": 'Maddeleri ışığı geçirme durumlarına göre sınıflandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Cam saydam, tahta opak gibi bir maddeyi ışık geçirme durumuna göre tanıma; tek adım.',
                        "orta": 'Verilen maddeleri saydam, yarı saydam, opak olarak gözleme dayalı sınıflandırma.',
                        "zor": 'Işık geçirme gözlem sonuçlarını çözümleyip belirsiz maddeyi ölçüte göre sınıflandırıp gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.5.4.3.1',
                    "metin": 'Tam gölgeye yönelik bilimsel gözlem yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Işık kaynağının önündeki cismin arkasında gölge oluştuğunu hatırlama; tek adım.',
                        "orta": 'Kaynak-cisim-perde düzeneğinde tam gölgenin nasıl oluştuğunu gözleme dayalı açıklama.',
                        "zor": 'Kaynak/cisim uzaklığı değişince tam gölge boyutundaki değişimi gözlemle çözümleyip neden-sonuçla açıklama.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-5-unite-5-maddenin-dogasi',
            "grade": 5,
            "no": 5,
            "name": 'Maddenin Doğası',
            "kazanimlar": [
                {
                    "kod": 'FB.5.5.1.1',
                    "metin": 'Maddeleri tanecikli, boşluklu ve hareketli yapısına göre sınıflandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Maddenin taneciklerden oluştuğunu veya tanecikler arası boşluk olduğunu hatırlama; tek bilgi.',
                        "orta": 'Katı, sıvı, gazın tanecik modelini boşluk ve hareket açısından verilen görselle ilişkilendirme.',
                        "zor": 'Farklı hâllerin tanecik düzenini boşluk-hareket ölçütleriyle çözümleyip yanlış modeli gerekçeyle düzeltme.',
                    },
                },
                {
                    "kod": 'FB.5.5.2.1',
                    "metin": 'Isı ve sıcaklık kavramlarını karşılaştırabilme',
                    "difficulty_hints": {
                        "kolay": 'Sıcaklığın termometreyle ölçüldüğünü veya ısının enerji olduğunu hatırlama; tek adım.',
                        "orta": 'Verilen bir örnekte ısı ile sıcaklığı ayırt edip birim/ölçüm farkıyla ilişkilendirme.',
                        "zor": 'Aynı sıcaklıkta farklı kütleli suların ısı miktarını karşılaştıran senaryoyu çok adımlı değerlendirme.',
                    },
                },
                {
                    "kod": 'FB.5.5.2.2',
                    "metin": 'Sıcaklığı farklı olan sıvıların karıştırılması sonucu ısı alışverişi olduğuna yönelik bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Sıcak ve soğuk su karışınca ortak sıcaklığa gelindiğini hatırlama; tek adım.',
                        "orta": 'Verilen sıcaklık değerlerinden karışım sonrası ısının sıcaktan soğuğa aktığını çıkarma.',
                        "zor": 'Farklı kütle ve sıcaklıktaki sıvıların karışım verisini çözümleyip son sıcaklığı gerekçeyle tahmin etme.',
                    },
                },
                {
                    "kod": 'FB.5.5.3.1',
                    "metin": 'Maddenin ısı etkisiyle hâl değiştirebileceğini bilimsel gözleme dayalı tahmin edebilme',
                    "difficulty_hints": {
                        "kolay": 'Buzun ısınınca eriyip suya döndüğünü hatırlama; tek hâl değişimi tanıma.',
                        "orta": 'Verilen ısıtma/soğutma durumunda oluşacak hâl değişimini (erime, buharlaşma) tahmin etme.',
                        "zor": 'Isı-zaman gözlem verisinden hâl değişimi basamaklarını çözümleyip beklenen sonucu gerekçeyle öngörme.',
                    },
                },
                {
                    "kod": 'FB.5.5.4.1',
                    "metin": 'Maddeleri ısı iletimi bakımından sınıflandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Metalin ısıyı iyi, tahtanın kötü ilettiğini hatırlama; tek madde tanıma.',
                        "orta": 'Verilen maddeleri iyi ve kötü ısı iletkeni olarak deney gözlemiyle sınıflandırma.',
                        "zor": 'Farklı maddelerin ısı iletim gözlem sonuçlarını çözümleyip günlük kullanım seçimini gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.5.5.4.2',
                    "metin": 'Isı yalıtımını gösteren model oluşturabilme',
                    "difficulty_hints": {
                        "kolay": 'Isı yalıtımının ısı kaybını azalttığını veya termosun yalıtım yaptığını hatırlama; tek bilgi.',
                        "orta": 'Verilen malzemelerle ısıyı koruyan basit yalıtım modelinin çalışma mantığını açıklama.',
                        "zor": 'Yalıtım modelinde malzeme seçimini test verisiyle karşılaştırıp en iyi tasarımı gerekçeyle savunma.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-5-unite-6-yasamimizdaki-elektrik',
            "grade": 5,
            "no": 6,
            "name": 'Yaşamımızdaki Elektrik',
            "kazanimlar": [
                {
                    "kod": 'FB.5.6.1.1',
                    "metin": 'Bir elektrik devresindeki elemanları sembollerinin olup olmamasına göre sınıflandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Pil, ampul, anahtarın devre elemanı olduğunu veya sembolünü tanıma; tek adım.',
                        "orta": 'Verilen elemanları sembolü olan ve olmayan biçimde sınıflandırıp sembolle eşleştirme.',
                        "zor": 'Karışık verilen eleman ve sembolleri sınıflandırıp yanlış eşleştirilen sembolü gerekçeyle düzeltme.',
                    },
                },
                {
                    "kod": 'FB.5.6.1.2',
                    "metin": 'Şemasını çizdiği elektrik devresine uygun deney yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Basit bir devre şemasında pil-ampul-anahtarın bağlı olduğunu tanıma; tek adım.',
                        "orta": 'Verilen devre şemasına uygun gerçek bağlantıyı kurup ampulün yanıp yanmayacağını çıkarma.',
                        "zor": 'Şema ile kurulan devreyi karşılaştırıp açık/kapalı devre hatasını çözümleyip gerekçeyle düzeltme.',
                    },
                },
                {
                    "kod": 'FB.5.6.2.1',
                    "metin": 'Bir elektrik devresindeki ampul parlaklığını etkileyen değişkenlerin neler olduğuna ilişkin hipotez oluşturabilme',
                    "difficulty_hints": {
                        "kolay": 'Ampul parlaklığının pil sayısına bağlı olabileceğini hatırlama; tek değişken tanıma.',
                        "orta": 'Verilen devre karşılaştırmasından parlaklığı etkileyen bir değişkeni (pil/ampul sayısı) belirleyip hipotez kurma.',
                        "zor": 'Birden çok değişkeni kontrol ederek parlaklık için test edilebilir hipotez oluşturup gerekçelendirme.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-5-unite-7-surdurulebilir-yasam-ve-geri-donusum',
            "grade": 5,
            "no": 7,
            "name": 'Sürdürülebilir Yaşam ve Geri Dönüşüm',
            "kazanimlar": [
                {
                    "kod": 'FB.5.7.1.1',
                    "metin": 'Evsel atıklarda geri dönüştürülebilen ve dönüştürülemeyen maddeleri sınıflandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Kağıt/cam geri dönüşür, pil dönüşmez gibi bir evsel atığı doğru gruplama; tek adım.',
                        "orta": 'Verilen evsel atıkları geri dönüştürülebilen ve dönüştürülemeyen olarak ölçüte göre sınıflandırma.',
                        "zor": 'Karışık atık listesini çözümleyip yanlış gruplanan atığı türü ve nedeniyle gerekçelendirerek düzeltme.',
                    },
                },
                {
                    "kod": 'FB.5.7.1.2',
                    "metin": 'Kaynakların etkili kullanımı konusunda geri dönüşümün önemli olduğuna yönelik bilimsel çıkarımda bulunabilme',
                    "difficulty_hints": {
                        "kolay": 'Geri dönüşümün kaynakları koruduğunu hatırlama; tek bilgi tanıma.',
                        "orta": 'Verilen bir örnekten geri dönüşümün doğal kaynak/enerji tasarrufu sağladığını çıkarma.',
                        "zor": 'Geri dönüşüm verisini çözümleyip kaynakların etkili kullanımına katkıyı çok adımlı bilimsel çıkarımla savunma.',
                    },
                },
                {
                    "kod": 'FB.5.7.1.3',
                    "metin": 'Yakın çevresinde atık yönetiminin uygulanabilirliğine ilişkin deneyimlerini yansıtabilme',
                    "difficulty_hints": {
                        "kolay": 'Evde atıkları ayrı biriktirmek gibi bir atık yönetimi davranışını hatırlama; tek örnek.',
                        "orta": 'Yakın çevredeki bir atık yönetimi uygulamasının işleyişini kendi deneyimiyle ilişkilendirerek açıklama.',
                        "zor": 'Çevresindeki atık yönetiminin uygulanabilirliğini deneyime dayanarak değerlendirip iyileştirme önerisini gerekçelendirme.',
                    },
                },
            ],
        },
    ],
    6: [
        {
            "unit_id": 'fen-6-unite-1-gunes-sistemi-ve-tutulmalar',
            "grade": 6,
            "no": 1,
            "name": 'Güneş Sistemi ve Tutulmalar',
            "kazanimlar": [
                {
                    "kod": 'FB.6.1.1.1',
                    "metin": 'Güneş sistemindeki gezegenleri niteliklerine göre sınıflandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir gezegenin adını veya iç/dış gezegen sınıfına ait olduğunu doğrudan tanıma; tek bilgi.',
                        "orta": "Verilen büyüklük, yapı veya Güneş'e uzaklık ölçütüne göre gezegeni doğru gruba yerleştirme.",
                        "zor": 'Birden çok niteliği (yapı, boyut, uzaklık) birlikte kullanarak tablodaki gezegenleri gerekçeyle sınıflandırma ve çeldirici eleme.',
                    },
                },
                {
                    "kod": 'FB.6.1.1.2',
                    "metin": 'Güneş sistemi ile ilgili bilimsel model oluşturabilme',
                    "difficulty_hints": {
                        "kolay": 'Güneş sistemi modelinde gezegenlerin Güneş çevresinde döndüğünü tanıma; tek adım.',
                        "orta": 'Basit bir model çiziminde gezegenlerin sıralaması veya göreli konumundaki bir hatayı fark etme.',
                        "zor": 'Ölçekli model ile gerçek uzaklık/boyut ilişkisini karşılaştırıp modelin sınırlarını değerlendirme ve düzeltme önerme.',
                    },
                },
                {
                    "kod": 'FB.6.1.2.1',
                    "metin": 'Güneş ve Ay tutulması ile ilgili bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Güneş veya Ay tutulmasının hangi gök cisimleri hizalandığında oluştuğunu doğrudan hatırlama.',
                        "orta": 'Verilen bir hizalanma şeklinden tutulmanın türünü (Güneş mi Ay mı) çıkarma; kısa gözlem yorumu.',
                        "zor": 'Güneş ve Ay tutulmasının neden her ay olmadığını yörünge eğikliğiyle ilişkilendirerek gerekçeli çıkarım yapma.',
                    },
                },
                {
                    "kod": 'FB.6.1.2.2',
                    "metin": 'Güneş ve Ay tutulması ile ilgili bilimsel model oluşturabilme',
                    "difficulty_hints": {
                        "kolay": 'Tutulma modelinde Güneş, Dünya, Ay dizilişini doğru tanıma; tek adım.',
                        "orta": 'Işık kaynağı ve gölge kullanarak kurulan modelde hangi tutulmanın gösterildiğini belirleme.',
                        "zor": 'Gölge konisi (umbra/penumbra) ile modeli açıklayıp tam/parçalı tutulma farkını gerekçelendirme ve model eksiğini eleştirme.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-6-unite-2-kuvvetin-etkisinde-hareket',
            "grade": 6,
            "no": 2,
            "name": 'Kuvvetin Etkisinde Hareket',
            "kazanimlar": [
                {
                    "kod": 'FB.6.2.1.1',
                    "metin": 'Bir cisme etki eden aynı doğrultudaki kuvvetler arasındaki ilişkileri açıklayarak bileşke kuvveti yapılandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Aynı yönlü iki kuvvetin toplanacağını doğrudan bilme; basit bileşke okuma.',
                        "orta": 'Aynı doğrultuda zıt yönlü kuvvetlerin farkını alarak bileşke kuvvetin büyüklük ve yönünü bulma.',
                        "zor": 'Çok kuvvetli senaryoda bileşkeyi hesaplayıp cismin denge/hareket durumunu gerekçelendirme, çeldirici yön hatası içeren.',
                    },
                },
                {
                    "kod": 'FB.6.2.1.2',
                    "metin": 'Dengelenmiş ve dengelenmemiş kuvvetlerin etkisi altındaki bir cismin hareketine yönelik deney yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Dengelenmiş kuvvet altında cismin duruş/sabit hızını tanıma; tek kavram.',
                        "orta": 'Basit deney düzeneğinde dengelenmemiş kuvvetin hareketi başlattığı/değiştirdiği durumu gözlemden çıkarma.',
                        "zor": 'Deney verilerinden kuvvet dengesini analiz edip değişken kontrolü ve sonuç yorumunu birlikte değerlendirme.',
                    },
                },
                {
                    "kod": 'FB.6.2.2.1',
                    "metin": 'Sürat ve hız kavramlarını karşılaştırabilme',
                    "difficulty_hints": {
                        "kolay": 'Sürat ile hızın farkını (yön içerir/içermez) doğrudan tanıma; tek bilgi.',
                        "orta": 'Verilen yol ve zamandan sürat hesaplayıp iki hareketi kısa günlük bağlamda karşılaştırma.',
                        "zor": 'Yön değiştiren çok adımlı harekette ortalama sürat ile hız arasındaki farkı hesaplayarak gerekçeli değerlendirme.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-6-unite-3-canlilarda-sistemler',
            "grade": 6,
            "no": 3,
            "name": 'Canlılarda Sistemler',
            "kazanimlar": [
                {
                    "kod": 'FB.6.3.1.1',
                    "metin": 'Eşeyli ve eşeysiz üremeyi karşılaştırabilme',
                    "difficulty_hints": {
                        "kolay": 'Eşeyli veya eşeysiz üremeye bir örnek canlıyı doğrudan eşleştirme; tek bilgi.',
                        "orta": 'Verilen üreme özelliğine bakarak eşeyli/eşeysiz ayrımını yapıp temel farkı açıklama.',
                        "zor": 'İki üreme türünün kalıtsal çeşitlilik açısından avantaj/dezavantajını senaryo üzerinden karşılaştırıp değerlendirme.',
                    },
                },
                {
                    "kod": 'FB.6.3.1.2',
                    "metin": 'Bitkilerde üreme, büyüme ve gelişme hakkında bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Bitkide üreme organının çiçek olduğunu veya tohumdan büyüdüğünü tanıma; tek adım.',
                        "orta": 'Tozlaşma-döllenme-tohum sürecindeki bir aşamayı verilen görselden çıkarım yaparak açıklama.',
                        "zor": 'Bitkinin üreme-büyüme aşamalarını çevresel etkenlerle ilişkilendirip gözlem verisinden gerekçeli çıkarım yapma.',
                    },
                },
                {
                    "kod": 'FB.6.3.1.3',
                    "metin": 'Tohumun çimlenmesine etki eden faktörlere ilişkin hipotez oluşturabilme',
                    "difficulty_hints": {
                        "kolay": 'Çimlenme için su, hava veya uygun sıcaklık gerektiğini doğrudan bilme; tek etken.',
                        "orta": 'Verilen basit çimlenme gözleminde tek değişkenin etkisine dair mantıklı bir hipotez kurma.',
                        "zor": 'Çok kaplı deney düzeneğinde değişkenleri kontrol edip kanıta dayalı hipotez oluşturarak sonucu gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.6.3.1.4',
                    "metin": 'Hayvanlarda üreme, büyüme ve gelişme hakkında bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Hayvanlarda yumurtayla/doğurarak çoğalmaya bir örnek tanıma; tek bilgi.',
                        "orta": 'Verilen gelişim (başkalaşım/doğrudan) örneğinden hayvanın üreme-gelişme biçimini çıkarma.',
                        "zor": 'Başkalaşım geçiren ve geçirmeyen hayvanların gelişimini karşılaştırıp yaşam döngüsü verisini analiz ederek çıkarım yapma.',
                    },
                },
                {
                    "kod": 'FB.6.3.1.5',
                    "metin": 'İnsanda üremeyi sağlayan yapı ve organlar arasındaki ilişkileri çözümleyebilme',
                    "difficulty_hints": {
                        "kolay": 'İnsanda üreme organ veya yapısının adını doğrudan tanıma; tek bilgi.',
                        "orta": 'Bir üreme yapısının görevini eşleştirip yapı-görev ilişkisini kısaca açıklama.',
                        "zor": 'Üreme yapıları arasındaki işlevsel ilişkiyi (yumurta-sperm-döllenme yolu) sıralı olarak çözümleyip senaryoda yorumlama.',
                    },
                },
                {
                    "kod": 'FB.6.3.2.1',
                    "metin": 'Sinir sisteminin görevlerini model üzerinde gözlemleyebilme',
                    "difficulty_hints": {
                        "kolay": 'Sinir sisteminin uyarıları ilettiğini veya beynin görevini doğrudan tanıma; tek bilgi.',
                        "orta": 'Basit bir uyarı-tepki örneğinde sinir sisteminin rolünü model üzerinden açıklama.',
                        "zor": 'Refleks ve istemli hareket yollarını modelde ayırt ederek uyarı-iletim-tepki zincirini gerekçeli çözümleme.',
                    },
                },
                {
                    "kod": 'FB.6.3.2.2',
                    "metin": 'İç salgı bezlerinin vücut için önemini yapılandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir iç salgı bezinin (ör. tiroit) adını veya hormon salgıladığını tanıma; tek bilgi.',
                        "orta": 'Verilen bir bezin salgısı ile vücuttaki etkisini eşleştirip önemini kısaca açıklama.',
                        "zor": 'Hormon dengesizliği senaryosunda bezin görevini analiz edip sonuçlarını neden-sonuç ilişkisiyle değerlendirme.',
                    },
                },
                {
                    "kod": 'FB.6.3.2.3',
                    "metin": 'Çocukluktan ergenliğe geçişte oluşan bedensel ve ruhsal değişimleri genelleyebilme',
                    "difficulty_hints": {
                        "kolay": 'Ergenlikte boy uzaması gibi bir bedensel değişimi doğrudan tanıma; tek örnek.',
                        "orta": 'Verilen değişimleri bedensel/ruhsal olarak ayırıp ergenlik dönemine ait olduğunu belirleme.',
                        "zor": 'Ergenlik değişimlerini hormonal nedenlerle ilişkilendirip bireysel farklılıkları senaryo üzerinden genelleyerek değerlendirme.',
                    },
                },
                {
                    "kod": 'FB.6.3.2.4',
                    "metin": 'Denetleyici ve düzenleyici sistemlerin sağlığı için yapılması gerekenlerle ilgili bilgi toplayabilme',
                    "difficulty_hints": {
                        "kolay": 'Sinir/hormonal sistem sağlığı için basit bir öneriyi (ör. yeterli uyku) tanıma; tek bilgi.',
                        "orta": 'Verilen bir yaşam alışkanlığının denetleyici sisteme etkisini kısa bağlamda açıklama.',
                        "zor": 'Farklı kaynaklardan derlenen bilgileri karşılaştırıp sistem sağlığı için gerekçeli öneriler oluşturarak değerlendirme.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-6-unite-4-isigin-yansimasi-ve-renkler',
            "grade": 6,
            "no": 4,
            "name": 'Işığın Yansıması ve Renkler',
            "kazanimlar": [
                {
                    "kod": 'FB.6.4.1.1',
                    "metin": 'Işığın farklı yüzeylerdeki yansıma olaylarına ilişkin bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Işığın pürüzsüz/pürüzlü yüzeyde yansıdığını doğrudan tanıma; tek kavram.',
                        "orta": 'Verilen yüzey türünden düzgün mü dağınık mı yansıma olacağını çıkarım yaparak açıklama.',
                        "zor": 'Düzgün ve dağınık yansımayı görsel/senaryo üzerinden karşılaştırıp günlük olayla gerekçeli ilişkilendirme.',
                    },
                },
                {
                    "kod": 'FB.6.4.1.2',
                    "metin": 'Işığın yansımasında gelen ışın, yansıyan ışın ve yüzeyin normali arasındaki ilişkiyi kanıt kullanarak açıklayabilme',
                    "difficulty_hints": {
                        "kolay": 'Gelme açısının yansıma açısına eşit olduğunu doğrudan bilme; tek kural.',
                        "orta": 'Verilen bir açıdan yansıyan ışının açısını bularak normal-ışın ilişkisini gösterme.',
                        "zor": 'Birden çok yansıma veya ölçüm verisiyle yansıma yasasını kanıtlayarak açı ilişkilerini çözümleme, çeldirici açı içeren.',
                    },
                },
                {
                    "kod": 'FB.6.4.2.1',
                    "metin": 'Günlük hayattaki ayna çeşitlerine ilişkin bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Düz, çukur veya tümsek aynadan birini günlük kullanımıyla doğrudan eşleştirme; tek bilgi.',
                        "orta": 'Verilen bir kullanım örneğinden (araç aynası vb.) hangi ayna çeşidinin uygun olduğunu çıkarma.',
                        "zor": 'Ayna çeşitlerinin görüntü özelliklerini karşılaştırıp belirli bir ihtiyaca en uygun aynayı gerekçeyle seçme.',
                    },
                },
                {
                    "kod": 'FB.6.4.3.1',
                    "metin": 'Işığın madde ile etkileşimi sonucunda soğurulabileceğini gözlemleyebilme',
                    "difficulty_hints": {
                        "kolay": 'Koyu renkli yüzeyin ışığı soğurduğunu doğrudan tanıma; tek kavram.',
                        "orta": 'Verilen basit gözlemde hangi cismin daha çok ışık soğurduğunu sonuçtan çıkarma.',
                        "zor": 'Soğurma-ısınma ilişkisini renk verisiyle analiz edip deney gözlemini gerekçeli olarak yorumlama.',
                    },
                },
                {
                    "kod": 'FB.6.4.3.2',
                    "metin": 'Beyaz ışığın tüm ışık renklerinin bileşiminden oluştuğuna ilişkin bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Beyaz ışığın prizmada renklere ayrıldığını doğrudan tanıma; tek bilgi.',
                        "orta": 'Prizma/gökkuşağı gözleminden beyaz ışığın renklerin bileşimi olduğu çıkarımını yapma.',
                        "zor": 'Renklerin birleşmesi ve ayrışması olaylarını karşılaştırıp beyaz ışığın bileşik yapısını kanıtla gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.6.4.3.3',
                    "metin": 'Cisimlerin siyah, beyaz ve renkli görünmesinin nedenini gözlem verileriyle açıklayabilme',
                    "difficulty_hints": {
                        "kolay": 'Kırmızı cismin kırmızı ışığı yansıttığını doğrudan tanıma; tek örnek.',
                        "orta": 'Verilen ışık-cisim durumunda cismin hangi renkte görüneceğini yansıma/soğurma ile açıklama.',
                        "zor": 'Renkli ışık altında cismin görünen rengini gözlem verisiyle çözümleyip beklenmeyen sonucu gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.6.4.3.4',
                    "metin": 'Güneş enerjisinin günlük hayat ve teknolojideki yenilikçi uygulamalarına ilişkin eleştirel düşünebilme',
                    "difficulty_hints": {
                        "kolay": 'Güneş panelinin güneş enerjisini kullandığını doğrudan tanıma; tek bilgi.',
                        "orta": 'Verilen bir güneş enerjisi uygulamasının günlük hayattaki yararını kısaca açıklama.',
                        "zor": 'Bir güneş enerjisi uygulamasının çevresel/ekonomik yarar ve sınırlarını karşılaştırıp eleştirel değerlendirme yapma.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-6-unite-5-maddenin-ayirt-edici-ozellikleri',
            "grade": 6,
            "no": 5,
            "name": 'Maddenin Ayırt Edici Özellikleri',
            "kazanimlar": [
                {
                    "kod": 'FB.6.5.1.1',
                    "metin": 'Isı etkisiyle maddelerin genleşip büzüleceğine yönelik bilimsel gözleme dayalı tahmin edebilme',
                    "difficulty_hints": {
                        "kolay": 'Isınan maddenin genleştiğini, soğuyanın büzüldüğünü doğrudan tanıma; tek kavram.',
                        "orta": 'Verilen günlük durumda (tel, ray) ısı etkisiyle boyut değişimini tahmin ederek açıklama.',
                        "zor": 'Genleşme-büzülmeyi katı/sıvı/gaz için karşılaştırıp gözleme dayalı tahmini gerekçelendirerek çeldiriciyi eleme.',
                    },
                },
                {
                    "kod": 'FB.6.5.2.1',
                    "metin": 'Maddelerin erime, donma ve kaynama noktasını gösteren deney yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Erime, donma veya kaynamanın hâl değişimi olduğunu doğrudan tanıma; tek bilgi.',
                        "orta": 'Basit ısınma deneyinde hangi aşamanın erime/kaynama olduğunu gözlemden belirleme.',
                        "zor": 'Sıcaklık-zaman grafiğindeki sabit bölgeleri hâl değişimiyle ilişkilendirip deneyi çok adımlı yorumlama.',
                    },
                },
                {
                    "kod": 'FB.6.5.3.1',
                    "metin": 'Yoğunluğa ilişkin hesaplamalar yaparak bilimsel veriye dayalı tahmin edebilme',
                    "difficulty_hints": {
                        "kolay": 'Yoğunluğun kütle bölü hacim olduğunu bilme; tek adımlı basit hesap.',
                        "orta": 'Verilen kütle ve hacimden yoğunluğu hesaplayıp maddenin batıp yüzeceğini tahmin etme.',
                        "zor": 'Yoğunluk verilerinden yüzme/batma ve sıvıda konum sıralamasını çok adımlı hesaplayarak gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.6.5.3.2',
                    "metin": 'Deneyler sonucunda çeşitli maddelerin yoğunluklarına ilişkin tümdengelimsel akıl yürütebilme',
                    "difficulty_hints": {
                        "kolay": 'Aynı maddenin yoğunluğunun miktardan bağımsız sabit olduğunu tanıma; tek bilgi.',
                        "orta": 'Verilen deney verisinden iki maddenin yoğunluk sırasını çıkararak karşılaştırma.',
                        "zor": 'Farklı kütle-hacim ölçümlerinden genel kurala tümdengelimle ulaşıp madde ayırt etmeyi gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.6.5.3.3',
                    "metin": 'Suyun katı ve sıvı hâllerine ait yoğunlukları karşılaştırarak bu durumun canlılar için önemi hakkında bilimsel çıkarımlar yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Buzun suda yüzdüğünü doğrudan tanıma; tek gözlem.',
                        "orta": 'Buz-su yoğunluk farkından buzun neden yüzdüğünü kısa bağlamda açıklama.',
                        "zor": 'Suyun donarken genleşmesinin göl canlıları için önemini yoğunluk verisiyle çok adımlı gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.6.5.3.4',
                    "metin": 'Yoğunluk ile ilgili bilimsel model oluşturabilme',
                    "difficulty_hints": {
                        "kolay": 'Yoğunluk modelinde ağır cismin dibe battığını tanıma; tek adım.',
                        "orta": 'Basit tanecik/kütle modeliyle iki maddenin yoğunluk farkını gösterme veya yorumlama.',
                        "zor": 'Yoğunluk modelini gerçek yüzme olaylarıyla karşılaştırıp modelin açıkladığı ve eksik kaldığı noktaları değerlendirme.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-6-unite-6-elektrigin-iletimi-ve-direnc',
            "grade": 6,
            "no": 6,
            "name": 'Elektriğin İletimi ve Direnç',
            "kazanimlar": [
                {
                    "kod": 'FB.6.6.1.1',
                    "metin": 'Maddelerin elektriği iletme durumlarını gösteren deney yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Metallerin elektriği ilettiğini, plastiğin iletmediğini doğrudan tanıma; tek bilgi.',
                        "orta": 'Basit devre deneyinde ampulün yanıp yanmamasından maddenin iletken/yalıtkan olduğunu çıkarma.',
                        "zor": 'Farklı maddelerin iletkenlik gözlem verilerini karşılaştırıp deney sonucunu güvenilirlik açısından değerlendirme.',
                    },
                },
                {
                    "kod": 'FB.6.6.2.1',
                    "metin": 'Elektrik devresindeki ampulün parlaklığının bağlı olduğu değişkenleri belirlemeye yönelik deney yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Pil sayısı artınca ampulün daha parlak yandığını doğrudan tanıma; tek değişken.',
                        "orta": 'Verilen basit devrede parlaklığı etkileyen değişkeni (pil/ampul sayısı) gözlemden belirleme.',
                        "zor": 'Değişken kontrollü deneyde parlaklığa etki eden çoklu etkenleri ayırt edip sonucu gerekçeli çözümleme.',
                    },
                },
                {
                    "kod": 'FB.6.6.2.2',
                    "metin": 'Ayarlanabilir direncin ampulün parlaklığına etkilerine yönelik bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Direnç artınca ampulün söndüğünü/kısıldığını doğrudan tanıma; tek kavram.',
                        "orta": 'Ayarlanabilir direncin konumu ile ampul parlaklığı arasındaki ilişkiyi gözlemden çıkarma.',
                        "zor": 'Direnç değişimi verisinden akım-parlaklık ilişkisini çok adımlı çözümleyip devre davranışını gerekçelendirme.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-6-unite-7-surdurulebilir-yasam-ve-etkilesim',
            "grade": 6,
            "no": 7,
            "name": 'Sürdürülebilir Yaşam ve Etkileşim',
            "kazanimlar": [
                {
                    "kod": 'FB.6.7.1.1',
                    "metin": 'Biyoçeşitliliğin doğal yaşam için önemini sorgulayabilme',
                    "difficulty_hints": {
                        "kolay": 'Biyoçeşitliliğin canlı türlerinin çeşitliliği olduğunu doğrudan tanıma; tek bilgi.',
                        "orta": 'Verilen bir ekosistem örneğinde biyoçeşitliliğin bir yararını sorgulayarak açıklama.',
                        "zor": 'Bir türün yok olmasının besin ağına etkisini çok adımlı analiz edip biyoçeşitliliğin önemini gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.6.7.1.2',
                    "metin": 'Biyoçeşitliliği tehdit eden faktörleri araştırma verilerine dayalı tahmin edebilme',
                    "difficulty_hints": {
                        "kolay": 'Biyoçeşitliliği tehdit eden bir faktörü (avlanma, kirlilik) doğrudan tanıma; tek bilgi.',
                        "orta": 'Verilen araştırma verisinden hangi faktörün tür sayısını azalttığını çıkarım yaparak tahmin etme.',
                        "zor": 'Çoklu tehdit verisini karşılaştırıp en etkili faktörü belirleyerek tahmini kanıtla gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.6.7.2.1',
                    "metin": 'Isınma amaçlı yakıt kullanımının insan ve çevre üzerine etkilerini tartışabilme',
                    "difficulty_hints": {
                        "kolay": 'Fosil yakıt yakmanın hava kirliliğine yol açtığını doğrudan tanıma; tek etki.',
                        "orta": 'Verilen bir yakıt kullanımı örneğinin insan/çevre sağlığına etkisini kısaca açıklama.',
                        "zor": 'Farklı yakıt türlerinin çevresel ve sağlık etkilerini karşılaştırıp tartışarak gerekçeli sonuç çıkarma.',
                    },
                },
                {
                    "kod": 'FB.6.7.2.2',
                    "metin": 'Yakın çevresindeki veya ülkemizdeki bir çevre problemine ilişkin çözüm üretebilme',
                    "difficulty_hints": {
                        "kolay": 'Bir çevre problemine (çöp, kirlilik) basit bir çözüm önerisini tanıma; tek adım.',
                        "orta": 'Verilen yerel çevre problemine uygun, uygulanabilir bir çözüm önerip nedenini açıklama.',
                        "zor": 'Bir çevre problemine çok yönlü çözüm geliştirip uygulanabilirlik ve etkisini değerlendirerek gerekçelendirme.',
                    },
                },
            ],
        },
    ],
    7: [
        {
            "unit_id": 'fen-7-unite-1-uzay-cagi',
            "grade": 7,
            "no": 1,
            "name": 'Uzay Çağı',
            "kazanimlar": [
                {
                    "kod": 'FB.7.1.1.1',
                    "metin": 'Uzay araştırmaları için geliştirilen teknolojileri karşılaştırabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir uzay teknolojisini (uydu, teleskop, roket) adıyla tanıma veya tek kullanım amacını eşleştirme.',
                        "orta": 'İki uzay teknolojisini amaç veya çalışma biçimi yönünden verilen bilgiye dayanarak karşılaştırma.',
                        "zor": 'Farklı uzay teknolojilerinin avantaj-sınırlarını senaryoda değerlendirip belirli göreve en uygun olanı gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.7.1.1.2',
                    "metin": 'Uzay gözlem araçları ile ilgili bilimsel model oluşturabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir uzay gözlem aracını (teleskop, uydu) tanıma veya temel görevini doğrudan belirtme.',
                        "orta": 'Optik ve radyo teleskop gibi gözlem araçlarını, verilen özelliklerinden yola çıkarak ilişkilendirme.',
                        "zor": 'Gözlem aracının çalışma modelini kurup neden yer yerine uzaya yerleştirildiğini çok adımlı gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.7.1.1.3',
                    "metin": 'Uzay araştırmalarının yol açabileceği problemleri çözebilme',
                    "difficulty_hints": {
                        "kolay": 'Uzay araştırmalarının yol açtığı bir problemi (uzay çöpü, maliyet) tanıma.',
                        "orta": 'Verilen bir uzay problemi için basit bir çözüm önerisini nedeniyle eşleştirme.',
                        "zor": 'Uzay kirliliği gibi bir soruna, olası çözümleri karşılaştırıp gerekçeli en uygun stratejiyi üretme.',
                    },
                },
                {
                    "kod": 'FB.7.1.2.1',
                    "metin": 'Yıldızların yaşamını açıklayarak yapılandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir yıldızın oluştuğu temel maddeyi (gaz-toz bulutu) veya bir evre adını hatırlama.',
                        "orta": 'Yıldızın yaşam evrelerini verilen görsel/sıra üzerinden doğru sıraya yerleştirme.',
                        "zor": 'Yıldızın kütlesine göre farklı yaşam sonu senaryolarını neden-sonuçla karşılaştırıp yorumlama.',
                    },
                },
                {
                    "kod": 'FB.7.1.2.2',
                    "metin": 'Yıldız, galaksi ve evren kavramlarını açıklayarak yapılandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Yıldız, galaksi ve evren kavramlarından birini tanımı veya örneğiyle eşleştirme.',
                        "orta": 'Yıldız, galaksi ve evreni büyüklük veya kapsama açısından doğru sıraya dizme.',
                        "zor": 'Bu kavramların içiçe hiyerarşisini bir senaryoda çözümleyip ölçek ilişkilerini gerekçeyle açıklama.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-7-unite-2-kuvvet-ve-enerjiyi-kesfedelim',
            "grade": 7,
            "no": 2,
            "name": 'Kuvvet ve Enerjiyi Keşfedelim',
            "kazanimlar": [
                {
                    "kod": 'FB.7.2.1.1',
                    "metin": 'Fiziksel anlamda yapılan işin bağlı olduğu faktörlere ilişkin bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Fiziksel işin yapıldığı durumu (kuvvet + yol) basit bir örnekte tanıma.',
                        "orta": 'Verilen kuvvet ve yol bilgisiyle bir durumda iş yapılıp yapılmadığına çıkarım yapma.',
                        "zor": 'Birkaç günlük durumu karşılaştırıp hangisinde fiziksel iş yapıldığını çeldiricili senaryoda gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.7.2.1.2',
                    "metin": 'Enerji çeşitlerinden kinetik ve potansiyel enerjiyi karşılaştırabilme',
                    "difficulty_hints": {
                        "kolay": 'Kinetik veya potansiyel enerjinin tanımını ya da tek örneğini doğrudan tanıma.',
                        "orta": 'Verilen bir durumda cismin kinetik mi potansiyel mi enerjiye sahip olduğunu belirleme.',
                        "zor": 'Hareket eden bir sistemde iki enerji türünün nasıl dönüştüğünü çok adımlı analiz edip karşılaştırma.',
                    },
                },
                {
                    "kod": 'FB.7.2.2.1',
                    "metin": 'Enerji dönüşümünden hareketle enerjinin korunduğu tümevarımsal akıl yürütebilme',
                    "difficulty_hints": {
                        "kolay": 'Bir enerji dönüşümü örneğini (elektrik→ışık) tanıma veya eşleştirme.',
                        "orta": 'Verilen düzenekte gerçekleşen enerji dönüşüm zincirini sırayla belirleme.',
                        "zor": 'Çoklu dönüşüm içeren sistemde enerjinin korunduğunu tümevarımla akıl yürütüp kayıpları yorumlama.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-7-unite-3-vucudumuzdaki-sistemler',
            "grade": 7,
            "no": 3,
            "name": 'Vücudumuzdaki Sistemler',
            "kazanimlar": [
                {
                    "kod": 'FB.7.3.1.1',
                    "metin": 'Sindirim sistemini oluşturan yapı ve organların görevlerini model üzerinde gözlemleyebilme',
                    "difficulty_hints": {
                        "kolay": 'Sindirim sistemi bir organını (mide, ince bağırsak) model üzerinde tanıma.',
                        "orta": 'Verilen bir sindirim organının görevini yapısıyla ilişkilendirerek belirleme.',
                        "zor": 'Besinin ağızdan sonuna izlediği yolu, organların görevlerini bağlayarak çok adımlı çözümleme.',
                    },
                },
                {
                    "kod": 'FB.7.3.1.2',
                    "metin": 'Sindirim sisteminin sağlığı için yapılması gerekenler konusunda bilgi toplayabilme',
                    "difficulty_hints": {
                        "kolay": 'Sindirim sağlığı için bir öneriyi (düzenli beslenme) tanıma.',
                        "orta": 'Verilen bir alışkanlığın sindirim sağlığına etkisini nedeniyle ilişkilendirme.',
                        "zor": 'Bir beslenme senaryosunu değerlendirip sindirim sağlığı açısından gerekçeli öneriler geliştirme.',
                    },
                },
                {
                    "kod": 'FB.7.3.2.1',
                    "metin": 'Dolaşım sistemini oluşturan yapı ve organların görevlerini model üzerinde gözlemleyebilme',
                    "difficulty_hints": {
                        "kolay": 'Dolaşım sistemi bir yapısını (kalp, damar) model üzerinde tanıma.',
                        "orta": 'Atardamar ve toplardamar gibi yapıların görevlerini verilen özellikle ilişkilendirme.',
                        "zor": 'Büyük-küçük kan dolaşımında kanın izlediği yolu organ görevleriyle bağlayarak çözümleme.',
                    },
                },
                {
                    "kod": 'FB.7.3.2.2',
                    "metin": 'Kan bağışının toplumsal dayanışma açısından önemini tartışabilme',
                    "difficulty_hints": {
                        "kolay": 'Kan bağışının bir yararını veya kime gerektiğini tanıma.',
                        "orta": 'Kan bağışının toplumsal katkısını verilen bir durumla ilişkilendirme.',
                        "zor": 'Kan bağışının dayanışma boyutunu bir senaryoda çok yönlü tartışıp gerekçeli değerlendirme.',
                    },
                },
                {
                    "kod": 'FB.7.3.2.3',
                    "metin": 'Dolaşım sisteminin sağlığı için yapılması gerekenler konusunda bilgi toplayabilme',
                    "difficulty_hints": {
                        "kolay": 'Dolaşım sağlığı için bir öneriyi (tuz-yağ azaltma, egzersiz) tanıma.',
                        "orta": 'Bir yaşam alışkanlığının kalp-damar sağlığına etkisini nedeniyle ilişkilendirme.',
                        "zor": 'Bir yaşam tarzı senaryosunu dolaşım sağlığı riskleri açısından değerlendirip gerekçeli öneri sunma.',
                    },
                },
                {
                    "kod": 'FB.7.3.3.1',
                    "metin": 'Solunum sistemini oluşturan yapı ve organların görevlerini model üzerinde gözlemleyebilme',
                    "difficulty_hints": {
                        "kolay": 'Solunum sistemi bir organını (akciğer, soluk borusu) model üzerinde tanıma.',
                        "orta": 'Verilen solunum organının görevini yapısıyla ilişkilendirerek belirleme.',
                        "zor": 'Havanın alınıp gaz değişimine kadarki yolunu organ görevlerini bağlayarak çok adımlı çözümleme.',
                    },
                },
                {
                    "kod": 'FB.7.3.3.2',
                    "metin": 'Solunum sisteminin sağlığı için yapılması gerekenler konusunda bilgi toplayabilme',
                    "difficulty_hints": {
                        "kolay": 'Solunum sağlığı için bir öneriyi (sigaradan kaçınma, temiz hava) tanıma.',
                        "orta": 'Bir davranışın (sigara, kirli hava) solunum sağlığına etkisini nedeniyle ilişkilendirme.',
                        "zor": 'Solunum sağlığını etkileyen çevre senaryosunu değerlendirip gerekçeli koruyucu öneriler geliştirme.',
                    },
                },
                {
                    "kod": 'FB.7.3.4.1',
                    "metin": 'Boşaltım sistemini oluşturan yapı ve organları model üzerinde gözlemleyebilme',
                    "difficulty_hints": {
                        "kolay": 'Boşaltım sistemi bir organını (böbrek) model üzerinde tanıma.',
                        "orta": 'Verilen boşaltım organının/yapısının görevini konumuyla ilişkilendirme.',
                        "zor": 'Kandan idrar oluşumuna kadarki süreci organların görevleriyle bağlayarak çok adımlı çözümleme.',
                    },
                },
                {
                    "kod": 'FB.7.3.4.2',
                    "metin": 'Boşaltım sisteminin sağlığı için yapılması gerekenler konusunda bilgi toplayabilme',
                    "difficulty_hints": {
                        "kolay": 'Boşaltım sağlığı için bir öneriyi (yeterli su içme) tanıma.',
                        "orta": 'Bir alışkanlığın (az su, aşırı tuz) böbrek sağlığına etkisini nedeniyle ilişkilendirme.',
                        "zor": 'Boşaltım sağlığını etkileyen bir yaşam senaryosunu değerlendirip gerekçeli öneriler sunma.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-7-unite-4-isigin-kirilmasi-ve-mercekler',
            "grade": 7,
            "no": 4,
            "name": 'Işığın Kırılması ve Mercekler',
            "kazanimlar": [
                {
                    "kod": 'FB.7.4.1.1',
                    "metin": 'Ortam değiştiren ışığın izlediği yolu gözlemleyerek kırılma olayına yönelik bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Işığın saydam ortam değiştirince kırıldığını veya kırılma örneğini tanıma.',
                        "orta": 'Verilen bir ışının az yoğun-çok yoğun ortam geçişinde nasıl kırıldığını belirleme.',
                        "zor": 'Kırılma açılarını ortam yoğunluğuyla ilişkilendirip düzenek gözleminden çok adımlı çıkarım yapma.',
                    },
                },
                {
                    "kod": 'FB.7.4.2.1',
                    "metin": 'Mercek çeşitlerine yönelik bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": 'İnce veya kalın kenarlı merceği görsel üzerinde tanıma.',
                        "orta": 'Verilen mercek tipinin ışığı toplama/dağıtma davranışını gözlemle ilişkilendirme.',
                        "zor": 'Mercek tipinin ışın yollarına etkisini analiz edip görüntü özelliklerini gerekçeyle çıkarma.',
                    },
                },
                {
                    "kod": 'FB.7.4.2.2',
                    "metin": 'Merceklerin günlük hayatta kullanım alanlarını örneklerle sınıflandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir mercekli aracı (gözlük, büyüteç) günlük kullanımıyla tanıma.',
                        "orta": 'Verilen kullanım örneğini ince/kalın kenarlı mercek türüne göre sınıflandırma.',
                        "zor": 'Farklı günlük araçları mercek türü ve amacına göre çeldiricili senaryoda sınıflandırıp gerekçelendirme.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-7-unite-5-maddenin-dogasina-yolculuk',
            "grade": 7,
            "no": 5,
            "name": 'Maddenin Doğasına Yolculuk',
            "kazanimlar": [
                {
                    "kod": 'FB.7.5.1.1',
                    "metin": 'Atomun yapısını ve yapısındaki temel parçacıkları çözümleyebilme',
                    "difficulty_hints": {
                        "kolay": 'Atomun temel parçacıklarından birini (proton, nötron, elektron) veya yükünü tanıma.',
                        "orta": 'Verilen parçacıkların atomdaki konumunu (çekirdek/katman) ve yükünü ilişkilendirme.',
                        "zor": 'Bir atomun parçacık sayılarından yola çıkıp yapısını çözümleyip yük durumunu gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.7.5.1.2',
                    "metin": 'Geçmişten günümüze atom kavramı ile ilgili bilimsel bilgilerin değişebileceğini sorgulayabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir atom modelini (Dalton, Bohr) bilim insanıyla veya sırayla tanıma.',
                        "orta": 'Atom modellerinin zamanla nasıl değiştiğini verilen bilgiyle ilişkilendirme.',
                        "zor": 'Atom modellerinin gelişimini karşılaştırıp bilimsel bilginin neden değiştiğini gerekçeyle sorgulama.',
                    },
                },
                {
                    "kod": 'FB.7.5.1.3',
                    "metin": 'Farklı molekül modelleri oluşturabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir molekül modelini (su, oksijen) atom sayısıyla tanıma.',
                        "orta": 'Verilen atomlardan basit bir molekül modelini doğru şekilde oluşturma.',
                        "zor": 'Farklı element atomlarından çok atomlu molekül modelleri kurup yapılarını karşılaştırma.',
                    },
                },
                {
                    "kod": 'FB.7.5.1.4',
                    "metin": 'Atomların elektron dizilimlerini yapılandırabilme',
                    "difficulty_hints": {
                        "kolay": 'İlk 3 katmanın alabileceği maksimum elektron sayısını hatırlama.',
                        "orta": 'Verilen atom numarasına göre elektronları katmanlara doğru dizme.',
                        "zor": 'Elektron dizilimini yapıp son katman elektron sayısından atomun davranışına çıkarım yapma.',
                    },
                },
                {
                    "kod": 'FB.7.5.2.1',
                    "metin": 'Saf maddeleri element ve bileşik olarak sınıflandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Verilen bir maddeyi element mi bileşik mi olduğunu doğrudan tanıma.',
                        "orta": 'Birkaç saf maddeyi model/formülüne göre element ve bileşik olarak sınıflandırma.',
                        "zor": 'Karışık örnekleri element-bileşik ölçütlerine göre çeldiricili senaryoda ayırıp gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.7.5.2.2',
                    "metin": 'Periyodik tablodaki ilk 18 elementin isimlerini sembolleriyle ifade edebilme',
                    "difficulty_hints": {
                        "kolay": 'İlk 18 elementten birinin adını sembolüyle eşleştirme.',
                        "orta": 'Verilen birkaç elementin ad-sembol eşleşmesini doğru tamamlama.',
                        "zor": 'Sembol karışıklığı içeren çeldiricili listede doğru ad-sembol eşleşmelerini ayırt etme.',
                    },
                },
                {
                    "kod": 'FB.7.5.2.3',
                    "metin": 'Periyodik tabloda grup ve periyotları karşılaştırabilme',
                    "difficulty_hints": {
                        "kolay": 'Periyodik tabloda grup (sütun) ve periyot (satır) kavramını tanıma.',
                        "orta": 'Verilen bir elementin grup ve periyodunu tablodaki konumundan belirleme.',
                        "zor": 'İki elementi grup-periyot konumlarına göre karşılaştırıp özellik benzerliğini gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.7.5.2.4',
                    "metin": 'Bileşiklerin isimlerini formülleriyle yapılandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Basit bir bileşiği (su=H2O) adıyla formülüne eşleştirme.',
                        "orta": 'Verilen bileşik adına karşılık gelen formülü atom sayısıyla doğru yazma.',
                        "zor": 'Birkaç bileşiğin ad-formül eşleşmesini çeldiriciler arasında çözümleyip doğru yapılandırma.',
                    },
                },
                {
                    "kod": 'FB.7.5.3.1',
                    "metin": 'Karışımları homojen ve heterojen olarak sınıﬂandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Verilen bir karışımı homojen mi heterojen mi olduğunu tanıma.',
                        "orta": 'Birkaç günlük karışımı görünüm özelliğine göre homojen-heterojen sınıflandırma.',
                        "zor": 'Benzer görünen karışımları ölçütlere göre çeldiricili senaryoda ayırt edip gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.7.5.3.2',
                    "metin": 'Çözünme hızına etki eden faktörler ile ilgili hipotez oluşturabilme',
                    "difficulty_hints": {
                        "kolay": 'Çözünme hızını etkileyen bir faktörü (sıcaklık, karıştırma) tanıma.',
                        "orta": 'Verilen bir faktörün çözünme hızını nasıl etkilediğini gözlemle ilişkilendirme.',
                        "zor": 'Değişkeni kontrol eden bir deney için çözünme hızına dair hipotez kurup gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.7.5.4.1',
                    "metin": 'Karışımları ayırmak için çeşitli deneyler yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir ayırma yöntemini (eleme, süzme, mıknatısla) tanıma.',
                        "orta": 'Verilen karışım için uygun ayırma yöntemini bileşen özelliğiyle eşleştirme.',
                        "zor": 'Çok bileşenli bir karışımı hangi yöntemlerle sırayla ayıracağını deney kurgusuyla planlama.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-7-unite-6-elektriklenme',
            "grade": 7,
            "no": 6,
            "name": 'Elektriklenme',
            "kazanimlar": [
                {
                    "kod": 'FB.7.6.1.1',
                    "metin": 'Elektriklenme ile ilgili bilgi toplayabilme',
                    "difficulty_hints": {
                        "kolay": 'Elektriklenmenin bir örneğini (saç-balon, cisim çekme) tanıma.',
                        "orta": 'Verilen bir elektriklenme durumunun neden oluştuğunu basitçe ilişkilendirme.',
                        "zor": 'Farklı elektriklenme gözlemlerini karşılaştırıp yük etkileşimini çok adımlı gerekçelendirme.',
                    },
                },
                {
                    "kod": 'FB.7.6.1.2',
                    "metin": 'Elektriklenme çeşitlerini belirlemeye yönelik deney yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Elektriklenme çeşitlerinden birini (sürtünme, dokunma, etki) tanıma.',
                        "orta": 'Verilen deney düzeneğinde hangi elektriklenme çeşidinin oluştuğunu belirleme.',
                        "zor": 'Bir deney tasarımından yola çıkıp elektriklenme çeşidini ve yük değişimini analiz etme.',
                    },
                },
                {
                    "kod": 'FB.7.6.1.3',
                    "metin": 'Cisimlerin elektrik yüklerini sınıflandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Cismin pozitif mi negatif mi yüklü olduğunu doğrudan tanıma.',
                        "orta": 'Verilen iki cismin çekim/itme davranışından yük işaretlerini ilişkilendirme.',
                        "zor": 'Birden çok cismin etkileşim gözleminden yüklerini çeldiricili senaryoda çözümleyip sınıflandırma.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-7-unite-7-surdurulebilir-yasam-ve-enerji',
            "grade": 7,
            "no": 7,
            "name": 'Sürdürülebilir Yaşam ve Enerji',
            "kazanimlar": [
                {
                    "kod": 'FB.7.7.1.1',
                    "metin": 'Besin zincirindeki canlıları arasındaki ilişkileri yapılandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Besin zincirinde bir canlının rolünü (üretici, tüketici) tanıma.',
                        "orta": 'Verilen canlıları enerji akışına göre doğru besin zinciri sırasına dizme.',
                        "zor": 'Bir canlının azalmasının besin zincirine etkisini neden-sonuçla çok adımlı çözümleme.',
                    },
                },
                {
                    "kod": 'FB.7.7.2.1',
                    "metin": 'Kaynakların tasarruflu kullanımının önemini sorgulayabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir doğal kaynağın tasarruflu kullanımına dair örneği tanıma.',
                        "orta": 'Verilen bir tüketim davranışının kaynak tasarrufuna etkisini nedeniyle ilişkilendirme.',
                        "zor": 'Kaynak kullanımı senaryosunu sürdürülebilirlik açısından değerlendirip gerekçeli öneriler geliştirme.',
                    },
                },
            ],
        },
    ],
    8: [
        {
            "unit_id": 'fen-8-unite-1-mevsimler-ve-iklim',
            "grade": 8,
            "no": 1,
            "name": 'Mevsimler ve İklim',
            "kazanimlar": [
                {
                    "kod": 'FB.8.1.1.1',
                    "metin": 'Dünya’nın Güneş etrafındaki hareketi ve eksen eğikliğinin sonuçları ile ilgili bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": "Dünya'nın Güneş etrafındaki hareketinin adını (dolanma) veya eksen eğikliği değerini doğrudan hatırlama.",
                        "orta": 'Eksen eğikliği ile ışınların geliş açısı arasında bağ kurma; verilen görselden mevsimi belirleme.',
                        "zor": "Farklı yarım kürelerde aynı tarihte ışın açısı, gölge boyu ve gündüz süresini çok adımlı yorumlama; 'Güneş'e uzaklık mevsim yapar' yanılgısını çeldirici olarak içeren LGS senaryosu.",
                    },
                },
                {
                    "kod": 'FB.8.1.2.1',
                    "metin": 'İklim ve hava olaylarını karşılaştırabilme',
                    "difficulty_hints": {
                        "kolay": 'İklim ve hava olayı kavramlarından birini tanıma veya tek bir örneği doğru sınıfa yerleştirme.',
                        "orta": 'Verilen tabloda süre ve alan ölçütünü kullanarak bir durumun iklim mi hava olayı mı olduğunu ayırt etme.',
                        "zor": "Uzun yıllık verilerle günlük gözlemi karşılaştıran gerçekçi senaryoda iklim-hava ayrımı yapma; 'bir günlük yağış iklimi gösterir' yanılgısını barındıran çeldiricili LGS sorusu.",
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-8-unite-2-yasami-kolaylastiran-kuvvet',
            "grade": 8,
            "no": 2,
            "name": 'Yaşamı Kolaylaştıran Kuvvet',
            "kazanimlar": [
                {
                    "kod": 'FB.8.2.1.1',
                    "metin": 'Basit makineleri sınıflandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Kaldıraç, makara, eğik düzlem gibi bir basit makinenin adını görselinden doğrudan tanıma.',
                        "orta": 'Verilen günlük araçları (el arabası, rampa, bisiklet) doğru basit makine türüne göre sınıflandırma.',
                        "zor": "Birden fazla basit makinenin birleştiği bir düzenekte türleri ayırt edip her birinin sağladığı kolaylığı gerekçelendirme; 'makine enerjiden kazandırır' yanılgısını içeren çeldiricili senaryo.",
                    },
                },
                {
                    "kod": 'FB.8.2.1.2',
                    "metin": 'Günlük yaşamda iş kolaylığı sağlayacak bilimsel model oluşturabilme',
                    "difficulty_hints": {
                        "kolay": 'Belirli bir işi kolaylaştırmak için hangi basit makinenin uygun olduğunu tek adımda seçme.',
                        "orta": 'Verilen günlük yaşam problemine (ağır yükü yukarı çıkarma) uygun basit makine modelini gerekçesiyle önerme.',
                        "zor": 'Kuvvetten mi yoldan mı kazanç gerektiğini analiz ederek en verimli düzeneği tasarlayıp seçenekleri karşılaştırma; iş korunumunu göz ardı eden çeldiricili LGS tasarım senaryosu.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-8-unite-3-yasamin-gizemi',
            "grade": 8,
            "no": 3,
            "name": 'Yaşamın Gizemi',
            "kazanimlar": [
                {
                    "kod": 'FB.8.3.1.1',
                    "metin": 'Nükleotid, gen, DNA ve kromozom kavramları arasındaki ilişkiyi yapılandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Nükleotid, gen, DNA, kromozom kavramlarından birinin tanımını doğrudan hatırlama.',
                        "orta": 'Bu kavramları büyükten küçüğe veya küçükten büyüğe doğru sıralayarak birbirini kapsama ilişkisini gösterme.',
                        "zor": "İç içe geçmiş yapıları bir şema üzerinde konumlandırıp kapsama ilişkilerini çok adımlı yorumlama; 'gen kromozomdan büyüktür' gibi kavram yanılgısına dayalı çeldiricili soru.",
                    },
                },
                {
                    "kod": 'FB.8.3.1.2',
                    "metin": 'DNA’nın yapısını model üzerinde gözlemleyebilme',
                    "difficulty_hints": {
                        "kolay": 'DNA modelinde şeker, fosfat veya baz gibi bir yapı birimini görselden tanıma.',
                        "orta": 'DNA modelinde bazların eşleşme kuralını (A-T, G-C) kullanarak karşı zinciri tamamlama.',
                        "zor": 'Verilen baz dizisinden karşı zinciri ve baz oranlarını hesaplayıp modelde yapıyı değerlendirme; yanlış baz eşleşmesi içeren çeldiricili LGS sorusu.',
                    },
                },
                {
                    "kod": 'FB.8.3.2.1',
                    "metin": 'Mitoz ve mayoz kavramları arasındaki ilişkiyi karşılaştırabilme',
                    "difficulty_hints": {
                        "kolay": 'Mitoz veya mayozdan birinin sonucunu (hücre sayısı, kromozom durumu) doğrudan hatırlama.',
                        "orta": 'Verilen bölünme görselinden mitoz mu mayoz mu olduğunu, sonuç hücre sayısı ve çeşitliliğe bakarak ayırt etme.',
                        "zor": "Bölünme türlerini kromozom sayısı, hücre sayısı, çeşitlilik ve gerçekleştiği yer bakımından çok ölçütlü karşılaştırma; 'mayoz vücut hücrelerinde olur' yanılgısını içeren çeldiricili senaryo.",
                    },
                },
                {
                    "kod": 'FB.8.3.3.1',
                    "metin": 'Kalıtımla ilgili kavramları yapılandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Gen, alel, genotip, fenotip, baskın, çekinik gibi bir kalıtım kavramının tanımını hatırlama.',
                        "orta": 'Verilen bir örnekte genotip ile fenotipi eşleştirme veya baskın-çekinik karakteri belirleme.',
                        "zor": 'Birden çok bireyin fenotipinden olası genotiplerini çıkarıp kavramları ilişkilendirme; heterozigot-homozigot karışımına dayalı çeldiricili LGS sorusu.',
                    },
                },
                {
                    "kod": 'FB.8.3.3.2',
                    "metin": 'Tek karakter çaprazlamaları ile ilgili problemler çözerek sonuçları değerlendirebilme',
                    "difficulty_hints": {
                        "kolay": 'Tek karakter çaprazlamasında homozigot bireylerin (örneğin AA x aa) yavru genotipini bulma.',
                        "orta": 'Verilen çaprazlamada Punnett karesi kullanarak yavruların fenotip oranını hesaplama.',
                        "zor": 'Yavru oranlarından geriye giderek ebeveyn genotiplerini bulup ihtimalleri değerlendiren çok adımlı LGS problemi; oran-olasılık karıştıran çeldiricili senaryo.',
                    },
                },
                {
                    "kod": 'FB.8.3.3.3',
                    "metin": 'Akraba evliliklerinin genetik sonuçlarını tartışabilme',
                    "difficulty_hints": {
                        "kolay": 'Akraba evliliğinin çekinik hastalık riskini artırdığı bilgisini doğrudan hatırlama.',
                        "orta": 'Basit soy ağacında akraba evliliğinden doğan çocukta çekinik hastalık ihtimalini yorumlama.',
                        "zor": "Soy ağacında taşıyıcıları belirleyip akraba evliliğinin hastalık olasılığına etkisini gerekçelendirme; 'akraba evliliği kesin hastalık yapar' yanılgısını içeren çeldiricili LGS sorusu.",
                    },
                },
                {
                    "kod": 'FB.8.3.4.1',
                    "metin": 'Mutasyonla ilgili bilgi toplayabilme',
                    "difficulty_hints": {
                        "kolay": 'Mutasyon veya modifikasyon kavramından birinin tanımını doğrudan hatırlama.',
                        "orta": 'Verilen örnekleri (UV ışını etkisi, güneşte bronzlaşma) mutasyon veya modifikasyon olarak ayırt etme.',
                        "zor": "Bir değişikliğin kalıtsal olup olmadığını nedeniyle analiz edip mutasyon-modifikasyon ayrımı yapma; 'her mutasyon zararlıdır' veya 'modifikasyon kalıtsaldır' yanılgısına dayalı çeldiricili senaryo.",
                    },
                },
                {
                    "kod": 'FB.8.3.4.2',
                    "metin": 'Canlıların yaşadıkları çevreye uyumlarına ilişkin bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir canlının yaşadığı ortama uyum sağlayan tek bir özelliğini (kutup ayısının kürkü) tanıma.',
                        "orta": 'Verilen ortam koşuluyla canlının uyum özelliği arasında neden-sonuç bağı kurma.',
                        "zor": "Farklı ortamlardaki canlıların uyum özelliklerini karşılaştırıp uyumun hayatta kalmaya etkisini çıkarımla değerlendirme; 'canlı isteyerek uyum geliştirir' yanılgısını içeren çeldiricili LGS senaryosu.",
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-8-unite-4-sesin-dunyasi',
            "grade": 8,
            "no": 4,
            "name": 'Sesin Dünyası',
            "kazanimlar": [
                {
                    "kod": 'FB.8.4.1.1',
                    "metin": 'Sesin oluşumuna yönelik bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Sesin titreşim sonucu oluştuğu bilgisini doğrudan hatırlama veya titreşen bir kaynağı tanıma.',
                        "orta": 'Verilen bir durumda (gergin telin çekilmesi) sesin nasıl oluştuğunu titreşimle açıklama.',
                        "zor": "Titreşim şiddeti, ortam ve kaynak ilişkisini bir düzenek üzerinden çıkarımla yorumlama; 'ses titreşim olmadan da oluşur' yanılgısını içeren çeldiricili senaryo.",
                    },
                },
                {
                    "kod": 'FB.8.4.1.2',
                    "metin": 'Sesin yayılabildiği ortamlara yönelik deney yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Sesin katı, sıvı, gaz gibi bir ortamda yayıldığı bilgisini doğrudan hatırlama.',
                        "orta": 'Boşlukta zil deneyinden yola çıkarak sesin yayılması için maddesel ortam gerektiği çıkarımını yapma.',
                        "zor": "Sesin farklı ortamlardaki yayılma hızını karşılaştıran deney sonuçlarını yorumlayıp değişkenleri kontrol etme; 'ses boşlukta da yayılır' yanılgısını içeren çeldiricili LGS deney sorusu.",
                    },
                },
                {
                    "kod": 'FB.8.4.1.3',
                    "metin": 'Sesin frekansına göre ince veya kalın olarak işitilmesine neden olan ses özellikleri ile ilgili deney yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Frekans ile ses inceliği (ince/kalın) arasındaki temel ilişkiyi doğrudan hatırlama.',
                        "orta": 'Verilen iki ses kaynağından frekansı yüksek olanın daha ince duyulacağını yorumlama.',
                        "zor": 'Farklı telli/borulu düzeneklerin frekansını uzunluk-kalınlıkla ilişkilendirip inceliği değerlendiren deney analizi; frekansı yükseklikle (şiddet) karıştıran çeldiricili senaryo.',
                    },
                },
                {
                    "kod": 'FB.8.4.2.1',
                    "metin": 'Ses ile ilgili değişkenlerin işitmeye etkisi hakkında hipotez oluşturabilme',
                    "difficulty_hints": {
                        "kolay": 'Sesin şiddeti veya frekansı gibi bir değişkenin işitmeyi etkilediği bilgisini hatırlama.',
                        "orta": 'Verilen bir gözlemden yola çıkarak ses değişkeni ile işitme arasında test edilebilir bir hipotez kurma.',
                        "zor": 'Ses şiddeti-mesafe-süre değişkenlerini içeren bir işitme deneyi için hipotez oluşturup kontrollü değişkenleri belirleme; bağımlı-bağımsız değişkeni karıştıran çeldiricili LGS senaryosu.',
                    },
                },
                {
                    "kod": 'FB.8.4.2.2',
                    "metin": 'Farklı maddeler ile etkileşimi sonucunda sesin iletilmesi, yansıması ve soğurulmasına ilişkin bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Sesin yansıması, soğurulması veya iletilmesinden birinin tanımını ya da örneğini tanıma.',
                        "orta": 'Verilen bir malzemenin (halı, çıplak duvar) sesi soğurma mı yansıtma mı yaptığını çıkarımla belirleme.',
                        "zor": "Bir salonun yankısını azaltmak için malzeme seçimini soğurma-yansıma özellikleriyle gerekçelendirme; 'sert yüzey sesi soğurur' yanılgısını içeren çeldiricili LGS senaryosu.",
                    },
                },
                {
                    "kod": 'FB.8.4.2.3',
                    "metin": 'Ses kirliliğini önlemeye yönelik bilimsel sorgulama yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Ses kirliliğine bir örnek verme veya basit bir önlemi (kulaklık sesini kısma) tanıma.',
                        "orta": 'Verilen bir ortamdaki ses kirliliği kaynağını belirleyip uygun bir önlem eşleştirme.',
                        "zor": 'Gerçek bir yerleşim senaryosunda ses kirliliği kaynaklarını analiz edip önceliklendirilmiş çözüm önerileri sorgulama; etkisiz önlemi mantıklı gösteren çeldiricili LGS sorusu.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-8-unite-5-periyodik-tablo-ve-maddenin-etkilesimi',
            "grade": 8,
            "no": 5,
            "name": 'Periyodik Tablo ve Maddenin Etkileşimi',
            "kazanimlar": [
                {
                    "kod": 'FB.8.5.1.1',
                    "metin": 'Elementleri periyodik tablo üzerinde metal, ametal, yarımetal ve soy gaz olarak sınıflandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir elementi periyodik tabloda metal, ametal, yarımetal veya soy gaz olarak doğrudan tanıma.',
                        "orta": 'Verilen özelliklerinden (parlaklık, iletkenlik) yola çıkarak bir elementi doğru sınıfa yerleştirme.',
                        "zor": "Tablodaki konum ve özelliklerden birden çok elementi sınıflandırıp grupların ortak özelliklerini çıkarımla karşılaştırma; 'tüm ametaller gazdır' yanılgısını içeren çeldiricili LGS sorusu.",
                    },
                },
                {
                    "kod": 'FB.8.5.2.1',
                    "metin": 'Fiziksel ve kimyasal değişimler ile ilgili bilimsel gözleme dayalı tahmin edebilme',
                    "difficulty_hints": {
                        "kolay": 'Fiziksel veya kimyasal değişime bir örneği (buzun erimesi, kağıdın yanması) doğrudan sınıflandırma.',
                        "orta": 'Verilen bir olayda yeni madde oluşup oluşmadığına bakarak değişim türünü gözleme dayalı tahmin etme.',
                        "zor": "Birden çok gözlem sonucunu (renk, gaz, geri dönüşüm) analiz ederek değişim türünü gerekçelendirme; 'hâl değişimi kimyasaldır' yanılgısını içeren çeldiricili LGS senaryosu.",
                    },
                },
                {
                    "kod": 'FB.8.5.3.1',
                    "metin": 'Kimyasal tepkimelerle ilgili bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Kimyasal tepkimede atomların korunduğu veya yeni madde oluştuğu bilgisini hatırlama.',
                        "orta": 'Verilen basit bir tepkimede girenler ve ürünleri ayırt edip atom sayısının korunduğunu yorumlama.',
                        "zor": "Bir tepkime denklemini kütlenin korunumu ilkesiyle analiz edip eksik giren/ürünü çıkarımla belirleme; 'tepkimede kütle kaybolur' yanılgısını içeren çeldiricili LGS sorusu.",
                    },
                },
                {
                    "kod": 'FB.8.5.3.2',
                    "metin": 'Kimyasal tepkimelerin günlük yaşamdaki etkilerine yönelik bilgi toplayabilme',
                    "difficulty_hints": {
                        "kolay": 'Yanma, paslanma gibi bir kimyasal tepkimenin günlük yaşamdaki bir örneğini tanıma.',
                        "orta": 'Verilen günlük olayları (ekşime, çürüme) hangi kimyasal tepkimeye bağlı olduklarıyla eşleştirme.',
                        "zor": 'Bir günlük yaşam sürecindeki kimyasal tepkimelerin yararlı/zararlı etkilerini analiz edip değerlendirme; tepkimenin olumlu-olumsuz yönünü karıştıran çeldiricili senaryo.',
                    },
                },
                {
                    "kod": 'FB.8.5.4.1',
                    "metin": 'Asit ve bazların genel özelliklerini karşılaştırabilme',
                    "difficulty_hints": {
                        "kolay": 'Asit veya bazların bir genel özelliğini (asit ekşidir, baz kaygandır) doğrudan hatırlama.',
                        "orta": 'Verilen özellikleri kullanarak bir maddenin asit mi baz mı olduğunu karşılaştırarak belirleme.',
                        "zor": 'Birden çok özelliği (tat, dokunma, metale etki, iletkenlik) tabloda karşılaştırıp asit-baz ayrımı yapma; asit-baz özelliklerini ters eşleyen çeldiricili LGS sorusu.',
                    },
                },
                {
                    "kod": 'FB.8.5.4.2',
                    "metin": 'Maddelerin asit veya baz olduğunu çeşitli ayıraçlar kullanarak bilimsel gözleme dayalı tahmin edebilme',
                    "difficulty_hints": {
                        "kolay": 'Turnusol veya benzeri bir ayıracın asit/bazda aldığı rengi doğrudan hatırlama.',
                        "orta": 'Verilen ayıraç renk değişiminden bir maddenin asit mi baz mı olduğunu gözleme dayalı tahmin etme.',
                        "zor": 'Birden çok maddenin farklı ayıraç sonuçlarını tabloda analiz edip asit/baz olduklarını çıkarımla belirleme; ayıraç rengini ters yorumlatan çeldiricili LGS deney sorusu.',
                    },
                },
                {
                    "kod": 'FB.8.5.4.3',
                    "metin": 'Maddelerin asitlik ve bazlık durumlarına ilişkin “pH” değerlerini kullanarak tümevarımsal akıl yürütebilme',
                    "difficulty_hints": {
                        "kolay": 'pH değerinin küçük olmasının asitliği, büyük olmasının bazlığı gösterdiğini doğrudan hatırlama.',
                        "orta": 'Verilen pH değerlerini kullanarak maddeleri asitlik-bazlık bakımından sıralama.',
                        "zor": "Farklı maddelerin pH değerlerinden tümevarımla asitlik gücü kuralı çıkarıp nötr durumu değerlendirme; 'pH büyükse daha asittir' yanılgısını içeren çeldiricili LGS sorusu.",
                    },
                },
                {
                    "kod": 'FB.8.5.4.4',
                    "metin": 'Asit ve bazların çeşitli maddeler üzerindeki etkilerine yönelik deney yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Asit veya bazın metale, cilde ya da mermere zarar verdiği gibi bir etkisini hatırlama.',
                        "orta": 'Verilen bir deneyde asidin metal üzerindeki etkisini (gaz çıkışı, aşınma) gözlemle yorumlama.',
                        "zor": 'Asit-baz etkilerini test eden bir deneyi değişkenleri kontrol ederek tasarlayıp sonuçları değerlendirme; nötrleşmeyi göz ardı eden çeldiricili LGS deney senaryosu.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-8-unite-6-elektrigin-yolculugu',
            "grade": 8,
            "no": 6,
            "name": 'Elektriğin Yolculuğu',
            "kazanimlar": [
                {
                    "kod": 'FB.8.6.1.1',
                    "metin": 'Ampullerin bağlanma durumunun ampul parlaklığına etkisine yönelik deney yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Ampullerin seri veya paralel bağlanmasından birinin adını devre görselinden tanıma.',
                        "orta": 'Verilen devrede ampul sayısı artınca seri bağlamada parlaklığın nasıl değişeceğini yorumlama.',
                        "zor": "Seri ve paralel bağlı devreleri parlaklık açısından karşılaştırıp bir bağlantı değişiminin etkisini çıkarımla değerlendirme; 'paralelde ampul sayısı parlaklığı azaltır' yanılgısını içeren çeldiricili LGS deney sorusu.",
                    },
                },
                {
                    "kod": 'FB.8.6.1.2',
                    "metin": 'Elektrik akımını tanımlayabilme',
                    "difficulty_hints": {
                        "kolay": 'Elektrik akımının yüklerin hareketi olduğu tanımını doğrudan hatırlama veya birimini (amper) tanıma.',
                        "orta": 'Verilen bir devrede akımın oluşması için gereken koşulu (kapalı devre) belirleme.',
                        "zor": 'Akımın yön, yük hareketi ve devre bütünlüğü ilişkisini bir düzenekte analiz edip çıkarım yapma; akımı gerilimle karıştıran çeldiricili senaryo.',
                    },
                },
                {
                    "kod": 'FB.8.6.1.3',
                    "metin": 'Bir devre elemanının uçları arasındaki potansiyel farkı (gerilimi) tanımlayabilme',
                    "difficulty_hints": {
                        "kolay": 'Potansiyel farkın (gerilim) tanımını hatırlama veya birimini (volt) tanıma.',
                        "orta": 'Verilen bir devrede gerilim kaynağının (pil) görevini potansiyel fark kavramıyla açıklama.',
                        "zor": 'Gerilimin akımla ilişkisini ve devredeki rolünü çok elemanlı bir düzenekte yorumlama; gerilimi akımla eşitleyen kavram yanılgılı çeldiricili LGS sorusu.',
                    },
                },
                {
                    "kod": 'FB.8.6.1.4',
                    "metin": 'Bir devre elemanının uçları arasındaki gerilim ile üzerinden geçen akım ilişkisine yönelik tümevarımsal akıl yürütebilme',
                    "difficulty_hints": {
                        "kolay": 'Gerilim artınca akımın da arttığı yönündeki temel ilişkiyi doğrudan hatırlama.',
                        "orta": 'Verilen gerilim-akım tablosundan iki değer arasında doğru orantı ilişkisini yorumlama.',
                        "zor": 'Gerilim-akım verilerinden tümevarımla ilişki (doğru orantı) çıkarıp bilinmeyen değeri hesaplayarak değerlendirme; grafik eğimini ters okutan çeldiricili LGS sorusu.',
                    },
                },
                {
                    "kod": 'FB.8.6.1.5',
                    "metin": 'Özgün bir aydınlatma aracı modeli oluşturabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir aydınlatma aracında bulunması gereken temel devre elemanını (pil, ampul, kablo) tanıma.',
                        "orta": 'Verilen malzemelerle çalışan basit bir aydınlatma devresi modelini şema üzerinde tamamlama.',
                        "zor": 'Belirli koşulları (taşınabilirlik, açma-kapama) karşılayan özgün bir aydınlatma modelini elemanları gerekçelendirerek tasarlama; çalışmayacak bağlantıyı doğru gösteren çeldiricili LGS senaryosu.',
                    },
                },
                {
                    "kod": 'FB.8.6.2.1',
                    "metin": 'Elektrik enerjisinin dönüştüğü enerjileri sınıflandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Elektrik enerjisinin dönüştüğü bir enerji türünü (ısı, ışık, ses, hareket) bir cihazla eşleştirme.',
                        "orta": 'Verilen günlük cihazları (ütü, radyo, vantilatör) dönüştürdükleri enerji türüne göre sınıflandırma.',
                        "zor": 'Bir cihazda gerçekleşen çoklu enerji dönüşümlerini ayırt edip istenen/istenmeyen dönüşümleri değerlendirme; tek dönüşüm varsayan çeldiricili LGS senaryosu.',
                    },
                },
                {
                    "kod": 'FB.8.6.2.2',
                    "metin": 'Elektrik enerjisinin ısı, ışık, ses veya hareket enerjisine dönüşümüne yönelik bir model oluşturabilme',
                    "difficulty_hints": {
                        "kolay": 'Elektrik enerjisini ısıya, ışığa veya harekete çeviren bir cihaz örneği verme.',
                        "orta": 'Verilen malzemelerle elektrik enerjisini belirli bir enerjiye dönüştüren basit bir model tasarlama.',
                        "zor": 'Enerji dönüşüm zincirini ve verimini dikkate alan bir model kurup istenmeyen kayıpları gerekçelendirme; enerjinin kaybolduğunu varsayan çeldiricili senaryo.',
                    },
                },
                {
                    "kod": 'FB.8.6.2.3',
                    "metin": 'Elektrik enerjisi üretim santrallerini sınıflandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir enerji santralini (hidroelektrik, termik, rüzgar) yenilenebilir/yenilenemez olarak tanıma.',
                        "orta": 'Verilen santralleri kullandıkları kaynağa göre yenilenebilir ve yenilenemez olarak sınıflandırma.',
                        "zor": "Santralleri kaynak, sürdürülebilirlik ve çevre etkisi ölçütleriyle çok yönlü sınıflandırıp karşılaştırma; 'hidroelektrik yenilenemez' gibi yanılgı içeren çeldiricili LGS sorusu.",
                    },
                },
                {
                    "kod": 'FB.8.6.2.4',
                    "metin": 'Elektrik enerjisi üretim santrallerinin avantaj ve dezavantajlarını tartışabilme',
                    "difficulty_hints": {
                        "kolay": 'Bir enerji santralinin tek bir avantaj veya dezavantajını doğrudan hatırlama.',
                        "orta": 'Verilen bir santralin avantaj ve dezavantajlarını kaynağına bakarak eşleştirme.',
                        "zor": 'İki farklı santrali maliyet, çevre ve süreklilik açısından tartışıp bir bölge için en uygun seçeneği gerekçelendirme; avantaj-dezavantajı ters kuran çeldiricili LGS senaryosu.',
                    },
                },
                {
                    "kod": 'FB.8.6.2.5',
                    "metin": 'Elektrik enerjisinin bilinçli ve tasarruflu kullanılmasının önemini tartışabilme',
                    "difficulty_hints": {
                        "kolay": 'Elektrik tasarrufu sağlayan bir davranışı (ışığı kapatma) doğrudan tanıma.',
                        "orta": 'Verilen ev senaryosunda gereksiz elektrik tüketimini belirleyip tasarruf önerisi eşleştirme.',
                        "zor": 'Bir hanenin tüketim verilerini analiz ederek en etkili tasarruf önlemlerini önceliklendirip tartışma; tasarruf etkisini abartan/küçümseyen çeldiricili LGS senaryosu.',
                    },
                },
            ],
        },
        {
            "unit_id": 'fen-8-unite-7-surdurulebilir-yasam-ve-madde-donguleri',
            "grade": 8,
            "no": 7,
            "name": 'Sürdürülebilir Yaşam ve Madde Döngüleri',
            "kazanimlar": [
                {
                    "kod": 'FB.8.7.1.1',
                    "metin": 'Bitkilerde besin üretiminde fotosentezin önemini yapılandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Fotosentezin girenlerini veya ürünlerini (karbondioksit, su, besin, oksijen) doğrudan hatırlama.',
                        "orta": 'Fotosentez şemasında girenler ve ürünleri eşleştirip besin üretimindeki rolünü yorumlama.',
                        "zor": "Fotosentezle solunumu madde alışverişi yönünden ilişkilendirip yaşam için önemini çıkarımla değerlendirme; 'bitkiler solunum yapmaz' yanılgısını içeren çeldiricili LGS sorusu.",
                    },
                },
                {
                    "kod": 'FB.8.7.1.2',
                    "metin": 'Fotosentez hızını etkileyen faktörler ile ilgili hipotez oluşturabilme',
                    "difficulty_hints": {
                        "kolay": 'Işık, sıcaklık veya karbondioksitin fotosentez hızını etkilediği bilgisini hatırlama.',
                        "orta": 'Verilen bir gözlemden yola çıkarak fotosentez hızını etkileyen bir faktör için test edilebilir hipotez kurma.',
                        "zor": 'Işık şiddeti-CO2-sıcaklık değişkenlerini içeren fotosentez deneyi için hipotez kurup kontrollü değişkenleri belirleme; değişkenleri karıştıran çeldiricili LGS deney senaryosu.',
                    },
                },
                {
                    "kod": 'FB.8.7.1.3',
                    "metin": 'Canlılarda solunumun önemini yapılandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Solunumun canlılara enerji sağladığı bilgisini doğrudan hatırlama.',
                        "orta": 'Solunum şemasında girenler (besin, oksijen) ve ürünleri (enerji, CO2, su) eşleştirip önemini yorumlama.',
                        "zor": 'Solunum ve fotosentezi enerji ve madde döngüsü açısından ilişkilendirip solunumun tüm canlılardaki önemini değerlendirme; solunumu sadece hayvanlara özgü sayan çeldiricili senaryo.',
                    },
                },
                {
                    "kod": 'FB.8.7.2.1',
                    "metin": 'Madde döngülerini şema üzerinde bilimsel çıkarım yapabilme',
                    "difficulty_hints": {
                        "kolay": 'Su, karbon veya oksijen döngüsünden birinin şemasında bir aşamayı doğrudan tanıma.',
                        "orta": 'Verilen madde döngüsü şemasında eksik oku veya aşamayı çıkarımla tamamlama.',
                        "zor": 'Bir döngü şemasında insan etkisiyle bozulan aşamayı belirleyip sonuçlarını çok adımlı çıkarımla yorumlama; döngü yönünü ters okutan çeldiricili LGS sorusu.',
                    },
                },
                {
                    "kod": 'FB.8.7.2.2',
                    "metin": 'Madde döngülerinin yaşam açısından önemini yapılandırabilme',
                    "difficulty_hints": {
                        "kolay": 'Madde döngülerinin doğadaki maddelerin sürekliliğini sağladığı bilgisini hatırlama.',
                        "orta": 'Verilen bir döngünün kesintiye uğramasının yaşam üzerindeki tek bir sonucunu yorumlama.',
                        "zor": 'Bir madde döngüsünün bozulmasının ekosisteme çok aşamalı etkilerini neden-sonuç zinciriyle değerlendirme; döngü öneminin abartıldığı/yok sayıldığı çeldiricili senaryo.',
                    },
                },
                {
                    "kod": 'FB.8.7.2.3',
                    "metin": 'Küresel iklim değişikliklerinin nedenlerini ve olası sonuçlarını tartışabilme',
                    "difficulty_hints": {
                        "kolay": 'Küresel iklim değişikliğinin bir nedenini (sera gazları) doğrudan tanıma.',
                        "orta": 'Verilen bir insan etkinliğini (fosil yakıt kullanımı) küresel iklim değişikliğiyle neden-sonuç olarak ilişkilendirme.',
                        "zor": "İklim değişikliğinin nedenlerini ve zincirleme sonuçlarını verilerle tartışıp çok değişkenli değerlendirme; 'ozon delinmesi ile sera etkisi aynıdır' yanılgısını içeren çeldiricili LGS sorusu.",
                    },
                },
                {
                    "kod": 'FB.8.7.2.4',
                    "metin": 'Ülkemizdeki küresel iklim değişikliğinin sebep olduğu bir probleme yönelik çözüm önerisi sunabilme',
                    "difficulty_hints": {
                        "kolay": 'Ülkemizde iklim değişikliğinin yol açtığı bir probleme (kuraklık, erozyon) örnek verme.',
                        "orta": 'Verilen bir yerel iklim problemine yönelik uygun bir çözüm önerisini eşleştirme.',
                        "zor": 'Ülkemize özgü bir iklim probleminin nedenlerini analiz edip uygulanabilir, öncelikli çözüm önerileri geliştirip savunma; etkisiz çözümü mantıklı gösteren çeldiricili LGS senaryosu.',
                    },
                },
            ],
        },
    ],
}


# ── Erişimciler (units.py deseni, fen'e özel) ────────────────────────────────
def get_units_for_grade(grade: int) -> list[FenUnit]:
    return list(FEN_CURRICULUM.get(grade, []))


def get_unit(grade: int, unit_id: str) -> FenUnit | None:
    for u in FEN_CURRICULUM.get(grade, []):
        if u["unit_id"] == unit_id:
            return u
    return None


def get_unit_kazanim(grade: int, unit_id: str, kazanim_kod: str) -> FenKazanim | None:
    unit = get_unit(grade, unit_id)
    if unit is None:
        return None
    for k in unit["kazanimlar"]:
        if k["kod"] == kazanim_kod:
            return k
    return None


def find_unit_by_kazanim(kazanim_kod: str) -> tuple[int, FenUnit] | None:
    for grade, units in FEN_CURRICULUM.items():
        for u in units:
            for k in u["kazanimlar"]:
                if k["kod"] == kazanim_kod:
                    return grade, u
    return None


def is_unit_available(grade: int, unit_id: str) -> bool:
    return get_unit(grade, unit_id) is not None
