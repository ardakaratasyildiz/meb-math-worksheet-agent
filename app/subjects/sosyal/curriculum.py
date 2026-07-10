"""Sosyal Bilgiler müfredatı — 2024 TYMM (Hayat Bilgisi 1-3 + Sosyal Bilgiler
4-7 + İnkılap Tarihi 8), ünite bazlı (otomatik üretildi).

Kaynak: knowledge_base/Sosyal/mufredat/*_2024_TYMM.pdf
Üretici: scripts/derive_sosyal_curriculum.py (deterministik, LLM'siz).
Kod: HB/SB/İTA.{sınıf}.{ünite}.{no}. difficulty_hints difficulty_hints.py'den gömülür.
"""
from __future__ import annotations

from typing import NotRequired, TypedDict


class SosKazanim(TypedDict):
    kod: str
    metin: str
    difficulty_hints: NotRequired[dict[str, str]]


class SosUnit(TypedDict):
    unit_id: str
    grade: int
    no: int
    name: str
    kazanimlar: list[SosKazanim]


SOS_CURRICULUM: dict[int, list[SosUnit]] = {
    1: [
        {
            "unit_id": 'sosyal-1-unite-1-ben-ve-okulum',
            "grade": 1,
            "no": 1,
            "name": 'Ben Ve Okulum',
            "kazanimlar": [
                {"kod": 'HB.1.1.1', "metin": 'Öğretmeni ve arkadaşlarıyla tanışabilme'},
                {"kod": 'HB.1.1.2', "metin": 'Okul ortamını tanıyabilme'},
                {"kod": 'HB.1.1.3', "metin": 'Sınıf ve okul ortamında kurallara uygun davranabilme'},
                {"kod": 'HB.1.1.4', "metin": 'Fiziksel özelliklerini ve temel duygularını açıklayabilme İÇERİK ÇERÇEVESİ Öğretmen ve Arkadaşlar Okul Ortamı Sınıf ve Okul Kuralları Fiziksel Özellikler ve Duygular Anahtar Kavramlar tanışma, arkadaş, iletişim,…'},
            ],
        },
        {
            "unit_id": 'sosyal-1-unite-2-sagligim-ve-guvenligim',
            "grade": 1,
            "no": 2,
            "name": 'Sağlığım Ve Güvenliğim',
            "kazanimlar": [
                {"kod": 'HB.1.2.1', "metin": 'Sağlıklı büyüme ve gelişme için yapması gerekenleri belirleyebilme'},
                {"kod": 'HB.1.2.2', "metin": 'Kişisel alanının sınırlarını belirleyebilme'},
                {"kod": 'HB.1.2.3', "metin": 'Temel trafik kurallarına uygun davranabilme'},
                {"kod": 'HB.1.2.4', "metin": 'Acil durumlarda yapılması gerekenleri belirleyebilme İÇERİK ÇERÇEVESİ Sağlıklı Büyüme ve Gelişme Kişisel Alan Temel Trafik Kuralları Acil Durumlar Anahtar Kavramlar sağlıklı büyüme ve gelişme, kişisel alan, acil…'},
            ],
        },
        {
            "unit_id": 'sosyal-1-unite-3-ailem-ve-toplum',
            "grade": 1,
            "no": 3,
            "name": 'Ailem Ve Toplum',
            "kazanimlar": [
                {"kod": 'HB.1.3.1', "metin": 'Aile olmanın önemini fark edebilme'},
                {"kod": 'HB.1.3.2', "metin": 'Aile yaşamında nezaket ve görgü kurallarına uygun davranabilme'},
                {"kod": 'HB.1.3.3', "metin": 'Aile bireylerinin görev ve sorumluluklarını çözümleyebilme'},
            ],
        },
        {
            "unit_id": 'sosyal-1-unite-4-yasadigim-yer-ve-ulkem',
            "grade": 1,
            "no": 4,
            "name": 'Yaşadığım Yer Ve Ülkem',
            "kazanimlar": [
                {"kod": 'HB.1.4.4', "metin": 'Millî gün ve bayramlarda yaşadığı duyguları ifade edebilme" çıktısı ile ilgili konular işlenebilir. 1.2.1. PROGRAMLAR ARASI BİLEŞENLER (SOSYAL-DUYGUSAL ÖĞRENME BECERİLERİ, OKURYAZARLIK BECERİLERİ, DEĞERLER)…'},
                {"kod": 'HB.1.4.1', "metin": 'Yaşadığı yerin ve ülkemizin genel özelliklerini açıklayabilme'},
                {"kod": 'HB.1.4.2', "metin": 'Türk Bayrağı ve İstiklâl Marşı’nın önemini ifade edebilme'},
                {"kod": 'HB.1.4.3', "metin": 'Mustafa Kemal Atatürk’ün hayatıyla ilgili bilgileri ifade edebilme'},
                {"kod": 'HB.1.4.5', "metin": 'Dinî gün ve bayramlarda yaşadığı duyguları ifade edebilme İÇERİK ÇERÇEVESİ Yaşadığımız Yer ve Ülkemizin Genel Özellikleri Türk Bayrağı ve İstiklâl Marşı Mustafa Kemal Atatürk’ün Hayatı Millî Gün ve Bayramlar Dinî Gün…'},
            ],
        },
        {
            "unit_id": 'sosyal-1-unite-5-doga-ve-cevre',
            "grade": 1,
            "no": 5,
            "name": 'Doğa Ve Çevre',
            "kazanimlar": [
                {"kod": 'HB.1.5.1', "metin": 'Yakın çevresinde bulunan doğadaki varlıkları gözlemleyebilme'},
                {"kod": 'HB.1.5.2', "metin": 'Modeller üzerinden gök cisimlerini karşılaştırabilme'},
                {"kod": 'HB.1.5.3', "metin": 'Afet türlerini tanıyabilme'},
                {"kod": 'HB.1.5.4', "metin": 'Geri dönüştürülebilen atıkları sınıflandırabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-1-unite-6-bilim-teknoloji-ve-sanat',
            "grade": 1,
            "no": 6,
            "name": 'Bilim, Teknoloji Ve Sanat',
            "kazanimlar": [
                {"kod": 'HB.1.6.1', "metin": 'Bilimle ilgili merak ettiklerini sorabilme Sunulan bilimsel bir konu hakkında merak ettiği soruları sorar'},
                {"kod": 'HB.1.6.2', "metin": 'Teknoloji ile ilgili merak ettiklerini sorabilme Sunulan teknolojik bir konu hakkında merak ettiği soruları sorar'},
                {"kod": 'HB.1.6.3', "metin": 'Sanatla ilgili merak ettiklerini sorabilme Sunulan sanatsal bir konu hakkında merak ettiği soruları sorar. İÇERİK ÇERÇEVESİ Bilim ile İlgili Merak Edilenler Teknoloji ile İlgili Merak Edilenler Sanat ile İlgili Merak…'},
            ],
        },
    ],
    2: [
        {
            "unit_id": 'sosyal-2-unite-1-ben-ve-okulum',
            "grade": 2,
            "no": 1,
            "name": 'Ben Ve Okulum',
            "kazanimlar": [
                {"kod": 'HB.2.1.1', "metin": 'Arkadaşlık ilişkilerini düzenleyebilme'},
                {"kod": 'HB.2.1.2', "metin": 'Güçlü ve gelişime açık olduğu alanlara karar verebilme İÇERİK ÇERÇEVESİ Arkadaşlık İlişkilerini Etkileyen Duygu, Düşünce ve Davranışlar Güçlü ve Gelişime Açık Alanlar İletişim Kuralları Sınıf İçi Karar Alma Süreçleri…'},
                {"kod": 'HB.2.1.3', "metin": 'Öğretmen ve arkadaşlarıyla etkili iletişim kurabilme'},
                {"kod": 'HB.2.1.4', "metin": 'Sınıf içi karar alma süreçlerine katılım sağlayabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-2-unite-2-sagligim-ve-guvenligim',
            "grade": 2,
            "no": 2,
            "name": 'Sağlığım Ve Güvenliğim',
            "kazanimlar": [
                {"kod": 'HB.2.2.1', "metin": 'Sağlıklı büyüme ve gelişme ile alışkanlıkları arasındaki ilişkiyi çözümleyebilme'},
                {"kod": 'HB.2.2.2', "metin": 'Kişisel alanının sınırlarını koruyabilme'},
                {"kod": 'HB.2.2.3', "metin": 'Temel trafik işaret levhalarını tanıyabilme'},
                {"kod": 'HB.2.2.4', "metin": 'Acil bir durumda yetkililerle etkili iletişim kurabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-2-unite-3-ailem-ve-toplum',
            "grade": 2,
            "no": 3,
            "name": 'Ailem Ve Toplum',
            "kazanimlar": [
                {"kod": 'HB.2.3.1', "metin": 'Ailenin önemini yorumlayabilme'},
                {"kod": 'HB.2.3.2', "metin": 'Toplumsal yaşamda nezaket ve görgü kurallarına uygun davranabilme'},
                {"kod": 'HB.2.3.3', "metin": 'Yakın çevresinde üzerine düşen görev ve sorumlulukları günlük yaşamına yan- sıtabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-2-unite-4-yasadigim-yer-ve-ulkem',
            "grade": 2,
            "no": 4,
            "name": 'Yaşadığım Yer Ve Ülkem',
            "kazanimlar": [
                {"kod": 'HB.2.4.1', "metin": 'Yakın çevresinde bulunan tarihî mekân ve doğal güzellikleri belirleyebilme'},
                {"kod": 'HB.2.4.2', "metin": 'Yaşadığı yerin yönetim birimleri ile ilgili kaynaklardan bilgi toplayabilme'},
                {"kod": 'HB.2.4.3', "metin": 'Mustafa Kemal Atatürk’ün öğrencilik yıllarına ait anıları yorumlayabilme'},
                {"kod": 'HB.2.4.4', "metin": 'Millî gün ve bayramların önemini yorumlayabilme'},
                {"kod": 'HB.2.4.5', "metin": 'Dinî gün ve bayramların önemini yorumlayabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-2-unite-5-doga-ve-cevre',
            "grade": 2,
            "no": 5,
            "name": 'Doğa Ve Çevre',
            "kazanimlar": [
                {"kod": 'HB.2.5.1', "metin": 'Hava olayları ve mevsimler arasındaki ilişkiyi çözümleyebilme'},
                {"kod": 'HB.2.5.2', "metin": 'Doğadan yararlanarak yönünü belirleyebilme'},
                {"kod": 'HB.2.5.3', "metin": 'Afetlere karşı alınması gereken önlemlere ilişkin bilgi toplayabilme'},
                {"kod": 'HB.2.5.4', "metin": 'Kaynakları tasarruflu kullanmanın önemini değerlendirebilme'},
            ],
        },
        {
            "unit_id": 'sosyal-2-unite-6-bilim-teknoloji-ve-sanat',
            "grade": 2,
            "no": 6,
            "name": 'Bilim, Teknoloji Ve Sanat',
            "kazanimlar": [
                {"kod": 'HB.2.6.1', "metin": 'Bilim insanlarının bilime katkılarına yönelik verilen kaynaklardan bilgi toplaya- bilme'},
                {"kod": 'HB.2.6.2', "metin": 'Günlük yaşamda kullanılan teknolojik bir ürünün zaman içerisindeki değişimini karşılaştırabilme'},
                {"kod": 'HB.2.6.3', "metin": 'Sanatın günlük yaşamdaki yerini belirleyebilme İÇERİK ÇERÇEVESİ Bilim İnsanlarının Bilime Katkıları Teknolojik Ürünlerin Zaman İçerisindeki Değişimi Sanatın Günlük Yaşamdaki Yeri Anahtar Kavramlar bilim, teknoloji,…'},
            ],
        },
    ],
    3: [
        {
            "unit_id": 'sosyal-3-unite-1-ben-ve-okulum',
            "grade": 3,
            "no": 1,
            "name": 'Ben Ve Okulum',
            "kazanimlar": [
                {"kod": 'HB.3.1.1', "metin": 'Kendini geliştirmek istediği alana ilişkin plan yapabilme'},
                {"kod": 'HB.3.1.2', "metin": 'Okuldaki hak ve sorumluluklarına uygun davranabilme'},
                {"kod": 'HB.3.1.3', "metin": 'Çocuk haklarını tanıtmak için fikirlerini eyleme dönüştürebilme'},
            ],
        },
        {
            "unit_id": 'sosyal-3-unite-2-sagligim-ve-guvenligim',
            "grade": 3,
            "no": 2,
            "name": 'Sağlığım Ve Güvenliğim',
            "kazanimlar": [
                {"kod": 'HB.3.2.1', "metin": 'Sağlığını korumaya yönelik davranışlarını düzenleyebilme'},
                {"kod": 'HB.3.2.2', "metin": 'Güvenliğini tehdit eden bir durumla karşılaştığında yapması gerekenleri sorgu- layabilme'},
                {"kod": 'HB.3.2.3', "metin": 'Trafik kurallarına uymanın önemine ilişkin özgün ürünler oluşturabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-3-unite-3-ailem-ve-toplum',
            "grade": 3,
            "no": 3,
            "name": 'Ailem Ve Toplum',
            "kazanimlar": [
                {"kod": 'HB.3.3.1', "metin": 'Aile ve toplum arasındaki ilişkiyi çözümleyebilme'},
                {"kod": 'HB.3.3.2', "metin": 'Yardıma ihtiyacı olan bireylerin yaşamını kolaylaştırmak için fikirlerini eyleme dönüştürebilme'},
                {"kod": 'HB.3.3.3', "metin": 'Mesleklerin toplumsal yaşamdaki önemini yorumlayabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-3-unite-4-yasadigim-yer-ve-ulkem',
            "grade": 3,
            "no": 4,
            "name": 'Yaşadığım Yer Ve Ülkem',
            "kazanimlar": [
                {"kod": 'HB.3.4.1', "metin": 'Yakın çevresindeki tarihî mekân ve doğal güzelliklerin korunmasının önemini fark edebilme'},
                {"kod": 'HB.3.4.2', "metin": 'Ülkemizin yönetim şekli ile ilgili kaynaklardan bilgi toplayabilme'},
                {"kod": 'HB.3.4.3', "metin": 'Mustafa Kemal Atatürk’ün kişilik özelliklerini çözümleyebilme'},
                {"kod": 'HB.3.4.4', "metin": 'Millî birlik ve beraberliğimizin toplum hayatına katkılarını açıklayabilme İÇERİK ÇERÇEVESİ Tarihî Mekân ve Doğal Güzellikler Ülkemizin Yönetim Şekli Mustafa Kemal Atatürk’ün Kişilik Özellikleri Millî Birlik ve…'},
            ],
        },
        {
            "unit_id": 'sosyal-3-unite-5-doga-ve-cevre',
            "grade": 3,
            "no": 5,
            "name": 'Doğa Ve Çevre',
            "kazanimlar": [
                {"kod": 'HB.3.5.1', "metin": 'Doğadaki varlıkların insan yaşamı için önemini yorumlayabilme'},
                {"kod": 'HB.3.5.2', "metin": 'Krokiyi kullanarak bulunduğu yerin konumunu algılayabilme'},
                {"kod": 'HB.3.5.3', "metin": 'Afetlere yönelik yapılması gerekenleri sınıflandırabilme Afetlere yönelik yapılması gerekenleri afet öncesi, sırası ve sonrasında yapılması gerekenler olarak ayırt eder'},
                {"kod": 'HB.3.5.4', "metin": 'Çevresel sürdürülebilirliğe yönelik kaynaklardan bilgi toplayabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-3-unite-6-bilim-teknoloji-ve-sanat',
            "grade": 3,
            "no": 6,
            "name": 'Bilim, Teknoloji Ve Sanat',
            "kazanimlar": [
                {"kod": 'HB.3.6.1', "metin": 'Bilimsel gelişmelerin günlük yaşama etkisini yorumlayabilme'},
                {"kod": 'HB.3.6.2', "metin": 'Teknolojik gelişmelerin günlük yaşama etkisini çözümleyebilme'},
                {"kod": 'HB.3.6.3', "metin": 'Sanatçıların sanata katkılarına yönelik verilen kaynaklardan bilgi toplayabilme'},
            ],
        },
    ],
    4: [
        {
            "unit_id": 'sosyal-4-unite-1-birlikte-yasamak',
            "grade": 4,
            "no": 1,
            "name": 'Birlikte Yaşamak',
            "kazanimlar": [
                {"kod": 'SB.4.1.1', "metin": 'Sosyal bilgiler dersinin hayatına sunacağı katkıları yorumlayabilme'},
                {"kod": 'SB.4.1.2', "metin": 'Bireysel özelliklere saygı duymanın önemine ilişkin çıkarım yapabilme'},
                {"kod": 'SB.4.1.3', "metin": 'Toplumsal birliği sürdürmeye yönelik fikir üretebilme'},
            ],
        },
        {
            "unit_id": 'sosyal-4-unite-2-evimiz-dunya',
            "grade": 4,
            "no": 2,
            "name": 'Evimiz Dünya',
            "kazanimlar": [
                {"kod": 'SB.4.2.1', "metin": 'Konum ve yön bulurken haritaları kullanabilme'},
                {"kod": 'SB.4.2.2', "metin": 'Yakın çevresinden hareketle doğa ve insan ilişkisini çözümleyebilme'},
                {"kod": 'SB.4.2.3', "metin": 'Afetlerin etkilerini azaltma konusunda yapılabileceklere ilişkin oluşturduğu ürünü paylaşabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-4-unite-3-ortak-mirasimiz',
            "grade": 4,
            "no": 3,
            "name": 'Ortak Mirasımız',
            "kazanimlar": [
                {"kod": 'SB.4.3.1', "metin": 'Geçmişten günümüze çocuk oyun ve oyuncaklarının değişimini karşılaştırabilme'},
                {"kod": 'SB.4.3.2', "metin": 'Aile tarihini yansıtan bir ürün oluşturabilme'},
                {"kod": 'SB.4.3.3', "metin": 'Yakın çevresindeki ortak miras ögelerini tanımanın önemini yorumlayabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-4-unite-4-yasayan-demokrasimiz',
            "grade": 4,
            "no": 4,
            "name": 'Yaşayan Demokrasimiz',
            "kazanimlar": [
                {"kod": 'SB.4.4.1', "metin": 'Cumhuriyetin ilanına giden yolda Mustafa Kemal Atatürk’ün ve Türk milletinin yaptığı fedakârlıkları yorumlayabilme'},
                {"kod": 'SB.4.4.2', "metin": 'Cumhuriyetin getirdiği değişimlerin hayatımıza katkılarını yorumlayabilme'},
                {"kod": 'SB.4.4.3', "metin": 'Okulda karar alma ve demokratik katılım süreçlerine ilişkin fikir üretebilme'},
            ],
        },
        {
            "unit_id": 'sosyal-4-unite-5-hayatimizdaki-ekonomi',
            "grade": 4,
            "no": 5,
            "name": 'Hayatımızdaki Ekonomi',
            "kazanimlar": [
                {"kod": 'SB.4.5.1', "metin": 'Doğal kaynakların tüketimi ile ilgili grafik yorumlayabilme'},
                {"kod": 'SB.4.5.2', "metin": 'İstek ve ihtiyaçları arasındaki bilinçli seçimleri hayatına yansıtabilme'},
                {"kod": 'SB.4.5.3', "metin": 'Bir ürünün üretim, dağıtım ve tüketim süreçlerini çözümleyebilme'},
            ],
        },
        {
            "unit_id": 'sosyal-4-unite-6-teknoloji-ve-sosyal-bilimler',
            "grade": 4,
            "no": 6,
            "name": 'Teknoloji Ve Sosyal Bilimler',
            "kazanimlar": [
                {"kod": 'SB.4.6.1', "metin": 'Çevrim içi ortamda uyulması gereken güvenlik kurallarını eylemlerine yansıtabilme'},
                {"kod": 'SB.4.6.2', "metin": 'Bilim insanlarının çocukluk hayatı ile kendi yaşamı arasında bağlantı kurabilme'},
            ],
        },
    ],
    5: [
        {
            "unit_id": 'sosyal-5-unite-1-birlikte-yasamak',
            "grade": 5,
            "no": 1,
            "name": 'Birlikte Yaşamak',
            "kazanimlar": [
                {"kod": 'SB.5.1.1', "metin": 'Dâhil olduğu gruplar ve bu gruplardaki rolleri arasındaki ilişkileri çözümleyebilme'},
                {"kod": 'SB.5.1.2', "metin": 'Kültürel özelliklere saygı duymanın birlikte yaşamaya etkisini yorumlayabilme'},
                {"kod": 'SB.5.1.3', "metin": 'Toplumsal birliği sürdürmeye yönelik yardımlaşma ve dayanışma faaliyetlerine katkı sağlayabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-5-unite-2-evimiz-dunya',
            "grade": 5,
            "no": 2,
            "name": 'Evimiz Dünya',
            "kazanimlar": [
                {"kod": 'SB.5.2.1', "metin": 'Yaşadığı ilin göreceli konum özelliklerini belirleyebilme'},
                {"kod": 'SB.5.2.2', "metin": 'Yaşadığı ilde doğal ve beşerî çevredeki değişimi neden ve sonuçlarıyla yorumlayabilme'},
                {"kod": 'SB.5.2.3', "metin": 'Yaşadığı ilde meydana gelebilecek afetlerin etkilerini azaltmaya yönelik farkındalık etkinlikleri düzenleyebilme'},
                {"kod": 'SB.5.2.4', "metin": 'Ülkemize komşu devletler hakkında bilgi toplayabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-5-unite-3-ortak-mirasimiz',
            "grade": 5,
            "no": 3,
            "name": 'Ortak Mirasımız',
            "kazanimlar": [
                {"kod": 'SB.5.3.1', "metin": 'Yaşadığı ildeki ortak miras ögelerine ilişkin oluşturduğu ürünü paylaşabilme'},
                {"kod": 'SB.5.3.2', "metin": 'Anadolu’da ilk yerleşimleri kuran toplumların sosyal hayatlarına yönelik bakış açısı geliştirebilme'},
                {"kod": 'SB.5.3.3', "metin": 'Mezopotamya ve Anadolu medeniyetlerinin ortak mirasa katkılarını karşılaştırabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-5-unite-4-yasayan-demokrasimiz',
            "grade": 5,
            "no": 4,
            "name": 'Yaşayan Demokrasimiz',
            "kazanimlar": [
                {"kod": 'SB.5.4.1', "metin": 'Demokrasi ve cumhuriyet kavramları arasındaki ilişkiyi çözümleyebilme'},
                {"kod": 'SB.5.4.2', "metin": 'Toplum düzenine etkisi bakımından etkin vatandaş olmanın önemine yönelik çıkarımda bulunabilme'},
                {"kod": 'SB.5.4.3', "metin": 'Temel insan hak ve sorumluluklarının önemini sorgulayabilme'},
                {"kod": 'SB.5.4.4', "metin": 'Bir ihtiyaç hâlinde veya sorun karşısında başvuru yapılabilecek kurumlar hakkında bilgi toplayabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-5-unite-5-hayatimizdaki-ekonomi',
            "grade": 5,
            "no": 5,
            "name": 'Hayatımızdaki Ekonomi',
            "kazanimlar": [
                {"kod": 'SB.5.5.1', "metin": 'Kaynakları verimli kullanmanın doğa ve insanlar üzerindeki etkisini yorumlayabilme'},
                {"kod": 'SB.5.5.2', "metin": 'İhtiyaç ve isteklerini karşılamak için gerekli bütçeyi planlayabilme'},
                {"kod": 'SB.5.5.3', "metin": 'Yaşadığı ildeki ekonomik faaliyetleri özetleyebilme'},
            ],
        },
        {
            "unit_id": 'sosyal-5-unite-6-teknoloji-ve-sosyal-bilimler',
            "grade": 5,
            "no": 6,
            "name": 'Teknoloji Ve Sosyal Bilimler',
            "kazanimlar": [
                {"kod": 'SB.5.6.1', "metin": 'Teknolojik gelişmelerin toplum hayatına etkilerini tartışabilme'},
                {"kod": 'SB.5.6.2', "metin": 'Teknolojik ürünlerin bilinçli kullanımının önemine ilişkin ürün oluşturabilme'},
            ],
        },
    ],
    6: [
        {
            "unit_id": 'sosyal-6-unite-1-birlikte-yasamak',
            "grade": 6,
            "no": 1,
            "name": 'Birlikte Yaşamak',
            "kazanimlar": [
                {"kod": 'SB.6.1.1', "metin": 'Dâhil olduğu grupların ve bu gruplardaki rollerinin zaman içerisinde değişebileceğine ilişkin çıkarım yapabilme'},
                {"kod": 'SB.6.1.2', "metin": 'Kültürel bağlarımızın ve millî değerlerimizin toplumsal birliğe etkisini yorumlayabilme'},
                {"kod": 'SB.6.1.3', "metin": 'Toplumsal hayatta karşılaşılan sorunlara yönelik çözüm önerilerini müzakere edebilme'},
            ],
        },
        {
            "unit_id": 'sosyal-6-unite-2-evimiz-dunya',
            "grade": 6,
            "no": 2,
            "name": 'Evimiz Dünya',
            "kazanimlar": [
                {"kod": 'SB.6.2.1', "metin": 'Ülkemizin, kıtaların ve okyanusların konum özelliklerini belirleyebilme'},
                {"kod": 'SB.6.2.2', "metin": 'Ülkemizin doğal ve beşerî çevre özellikleri arasındaki ilişkiyi çözümleyebilme'},
                {"kod": 'SB.6.2.3', "metin": 'Ülkemizin Türk dünyasıyla kültürel iş birliklerini yorumlayabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-6-unite-3-ortak-mirasimiz',
            "grade": 6,
            "no": 3,
            "name": 'Ortak Mirasımız',
            "kazanimlar": [
                {"kod": 'SB.6.3.1', "metin": 'Türkistan’da kurulan ilk Türk devletlerinin medeniyetimize katkılarını sorgulayabilme'},
                {"kod": 'SB.6.3.2', "metin": 'VII-XIII. yüzyıllar arasında İslam medeniyetinin eğitim, bilim, hukuk, kültür, sanat ve mimari alanlarında insanlığın ortak mirasına katkılarına dair akıl yürütebilme'},
                {"kod": 'SB.6.3.3', "metin": 'İslamiyet’in kabulüyle Türklerin sosyal ve kültürel hayatlarında meydana gelen değişimi dönemin bakış açısıyla değerlendirebilme'},
                {"kod": 'SB.6.3.4', "metin": 'XI-XIII. yüzyıllar arasında meydana gelen siyasi faaliyetler ve askerî mücadelelerin Anadolu’nun Türkleşmesi ve İslamlaşmasına etkisini özetleyebilme'},
            ],
        },
        {
            "unit_id": 'sosyal-6-unite-4-yasayan-demokrasimiz',
            "grade": 6,
            "no": 4,
            "name": 'Yaşayan Demokrasimiz',
            "kazanimlar": [
                {"kod": 'SB.6.4.1', "metin": 'Yönetimin karar alma sürecini etkileyen unsurları çözümleyebilme'},
                {"kod": 'SB.6.4.2', "metin": 'Toplumsal düzenin sürdürülmesinde temel hak ve sorumlulukların önemini yorumlayabilme'},
                {"kod": 'SB.6.4.3', "metin": 'Vatandaşlık haklarının kullanımında dijitalleşme ve teknolojik gelişmelerin etkilerini sorgulayabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-6-unite-5-hayatimizdaki-ekonomi',
            "grade": 6,
            "no": 5,
            "name": 'Hayatımızdaki Ekonomi',
            "kazanimlar": [
                {"kod": 'SB.6.5.1', "metin": 'Ülkemizin kaynakları ile ekonomik faaliyetler arasındaki ilişkiyi çözümleyebilme'},
                {"kod": 'SB.6.5.2', "metin": 'Ekonomik faaliyetler ve meslekler arasındaki ilişki hakkında çıkarımda bulunabilme'},
                {"kod": 'SB.6.5.3', "metin": 'Tasarladığı bir ürün için yatırım ve pazarlama proje önerisi hazırlayabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-6-unite-6-teknoloji-ve-sosyal-bilimler',
            "grade": 6,
            "no": 6,
            "name": 'Teknoloji Ve Sosyal Bilimler',
            "kazanimlar": [
                {"kod": 'SB.6.6.1', "metin": 'Ulaşım ve iletişim teknolojilerindeki gelişmelerin kültürel etkileşimdeki rolünü yapılandırabilme'},
                {"kod": 'SB.6.6.2', "metin": 'Bir ürün veya fikrin telif ve patent süreçleriyle ilgili bilgi toplayabilme'},
            ],
        },
    ],
    7: [
        {
            "unit_id": 'sosyal-7-unite-1-birlikte-yasamak',
            "grade": 7,
            "no": 1,
            "name": 'Birlikte Yaşamak',
            "kazanimlar": [
                {"kod": 'SB.7.1.2', "metin": 'Özel gereksinimli bireyler için fırsat eşitliğini sürdürmeye yönelik fikir üretebilme'},
                {"kod": 'SB.7.1.3', "metin": 'Türk toplumunun millî meseleler karşısında gösterdiği tutum ve davranışlara ilişkin çıkarım yapabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-7-unite-2-evimiz-dunya',
            "grade": 7,
            "no": 2,
            "name": 'Evimiz Dünya',
            "kazanimlar": [
                {"kod": 'SB.7.2.1', "metin": 'Küreselleşmenin insan ve toplum hayatında meydana getirdiği değişimi yorumlayabilme'},
                {"kod": 'SB.7.2.2', "metin": 'Bölgesel ve küresel sorunların çözümünde ülkemizin rolünü özetleyebilme'},
            ],
        },
        {
            "unit_id": 'sosyal-7-unite-3-ortak-mirasimiz',
            "grade": 7,
            "no": 3,
            "name": 'Ortak Mirasımız',
            "kazanimlar": [
                {"kod": 'SB.7.3.1', "metin": 'Osmanlı Devleti’nin cihan devleti hâline gelmesini sağlayan politikaları sorgulayabilme'},
                {"kod": 'SB.7.3.2', "metin": 'Değişen dünya dengeleri karşısında Osmanlı Devleti’nin uyguladığı yenilikleri neden ve sonuçlarıyla yorumlayabilme'},
                {"kod": 'SB.7.3.3', "metin": 'Osmanlı kültür ve medeniyet unsurlarına ilişkin oluşturduğu ürünü paylaşabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-7-unite-4-yasayan-demokrasimiz',
            "grade": 7,
            "no": 4,
            "name": 'Yaşayan Demokrasimiz',
            "kazanimlar": [
                {"kod": 'SB.7.4.1', "metin": 'Türkiye Cumhuriyeti’nin temel niteliklerini özetleyebilme'},
                {"kod": 'SB.7.4.2', "metin": 'Türkiye Cumhuriyeti Devleti’nin yönetim yapısını çözümleyebilme'},
                {"kod": 'SB.7.4.3', "metin": 'Ülkemizdeki demokrasinin gelişimini, demokrasinin temel ilkeleri açısından yorumlayabilme'},
                {"kod": 'SB.7.4.4', "metin": 'Demokrasinin uygulama sürecinde karşılaşılan sorunları özetleyebilme'},
            ],
        },
        {
            "unit_id": 'sosyal-7-unite-5-hayatimizdaki-ekonomi',
            "grade": 7,
            "no": 5,
            "name": 'Hayatımızdaki Ekonomi',
            "kazanimlar": [
                {"kod": 'SB.7.5.1', "metin": 'Millî kalkınma hamlelerini neden ve sonuçlarıyla yorumlayabilme'},
                {"kod": 'SB.7.5.2', "metin": 'Ekonomik gelişmişlik ile üretim, dağıtım ve tüketim döngüsü arasındaki ilişkiyi çözümleyebilme'},
            ],
        },
        {
            "unit_id": 'sosyal-7-unite-6-teknoloji-ve-sosyal-bilimler',
            "grade": 7,
            "no": 6,
            "name": 'Teknoloji Ve Sosyal Bilimler',
            "kazanimlar": [
                {"kod": 'SB.7.6.1', "metin": 'Bilimsel ve teknolojik gelişmelerin gelecekteki toplum hayatına etkilerine ilişkin öngörüde bulunabilme'},
                {"kod": 'SB.7.6.2', "metin": 'Örnek metinler üzerinden sosyal bilimlerin çalışma alanlarına dair genelleme yapabilme'},
                {"kod": 'SB.7.6.3', "metin": 'Toplumsal hayatta karşılaşabileceği bir probleme yönelik bilimsel sorgulama yapabilme'},
            ],
        },
    ],
    8: [
        {
            "unit_id": 'sosyal-8-unite-1-mustafa-kemalin',
            "grade": 8,
            "no": 1,
            "name": 'Mustafa Kemal’in',
            "kazanimlar": [
                {"kod": 'İTA.8.1.1', "metin": 'Öğrencilerin Osmanlı Devleti’nin XIX- XX. yüzyıllardaki sınırlarını haritalar üzerinden incelemeleri istenir (SBAB10.1) (OB4). İnceledik- leri haritalarda Osmanlı Devleti’nin sınırlarında meydana gelen değişime…'},
                {"kod": 'İTA.8.1.2', "metin": 'Çocuk, komutan ve devlet adamı olarak Atatürk’ün hayatına ilişkin oluşturduğu özgün ürünleri paylaşabilme'},
                {"kod": 'İTA.8.1.3', "metin": 'Mustafa Kemal’in kişilik özelliklerini özetleyebilme'},
            ],
        },
        {
            "unit_id": 'sosyal-8-unite-2-birinci-dunya-savasi',
            "grade": 8,
            "no": 2,
            "name": 'Birinci Dünya Savaşı',
            "kazanimlar": [
                {"kod": 'İTA.8.2.1', "metin": 'Birinci Dünya Savaşı’nın nedenlerini tarihsel bağlamına uygun olarak açıklaya- bilme'},
                {"kod": 'İTA.8.2.2', "metin": 'Osmanlı Devleti’nin Birinci Dünya Savaşı’na katılma sürecine ilişkin alternatif fikirler üretebilme'},
                {"kod": 'İTA.8.2.3', "metin": 'Osmanlı Devleti’nin Birinci Dünya Savaşı’nda savaştığı cephelerin savaşın gidi- şatına etkisini sorgulayabilme'},
                {"kod": 'İTA.8.2.4', "metin": 'Birinci Dünya Savaşı’nın sonuçlarını tablo, grafik, şekil ve diyagram üzerinden yorumlayabilme'},
                {"kod": 'İTA.8.2.5', "metin": 'Birinci Dünya Savaşı’nın Türk toplumuna etkilerine yönelik bakış açısı geliştire- bilme'},
            ],
        },
        {
            "unit_id": 'sosyal-8-unite-3-mill-mucadele',
            "grade": 8,
            "no": 3,
            "name": 'Millî Mücadele',
            "kazanimlar": [
                {"kod": 'İTA.8.3.1', "metin": 'Mondros Mütarekesi’ne karşı Osmanlı yönetiminin, Mustafa Kemal’in, aydınların ve halkın tutumunu karşılaştırabilme'},
                {"kod": 'İTA.8.3.2', "metin": 'Millî Mücadele’nin hazırlık sürecinde yapılan çalışmaların etkilerini değerlendi- rebilme'},
                {"kod": 'İTA.8.3.3', "metin": 'Millî Mücadele sürecinde meydana gelen siyasi ve askerî gelişmeleri neden ve sonuçlarıyla birlikte yorumlayabilme'},
                {"kod": 'İTA.8.3.4', "metin": 'Türk milletinin Millî Mücadele sürecindeki rolüne ilişkin oluşturduğu özgün ürünleri paylaşabilme'},
            ],
        },
        {
            "unit_id": 'sosyal-8-unite-4-turkiye-cumhuriyetinin-kurulusu',
            "grade": 8,
            "no": 4,
            "name": 'Türkiye Cumhuriyeti’nin Kuruluşu',
            "kazanimlar": [
                {"kod": 'İTA.8.4.1', "metin": 'Cumhuriyet’in ilanına kadar geçen süreçte meydana gelen siyasi ve diplomatik gelişmeleri özetleyebilme'},
                {"kod": 'İTA.8.4.2', "metin": 'Türk modernleşmesi çerçevesinde Atatürk’ün yaptığı inkılapları neden ve so- nuçlarıyla yorumlayabilme'},
                {"kod": 'İTA.8.4.3', "metin": 'Atatürk ilke ve inkılapları arasındaki ilişkiyi ortaya koyan özgün bir ürün oluş- turabilme'},
            ],
        },
    ],
}


def get_units_for_grade(grade: int) -> list[SosUnit]:
    return list(SOS_CURRICULUM.get(grade, []))


def get_unit(grade: int, unit_id: str) -> SosUnit | None:
    for u in SOS_CURRICULUM.get(grade, []):
        if u["unit_id"] == unit_id:
            return u
    return None


def get_unit_kazanim(grade: int, unit_id: str, kazanim_kod: str) -> SosKazanim | None:
    unit = get_unit(grade, unit_id)
    if unit is None:
        return None
    for k in unit["kazanimlar"]:
        if k["kod"] == kazanim_kod:
            return k
    return None


def find_unit_by_kazanim(kazanim_kod: str) -> tuple[int, SosUnit] | None:
    for grade, units in SOS_CURRICULUM.items():
        for u in units:
            for k in u["kazanimlar"]:
                if k["kod"] == kazanim_kod:
                    return grade, u
    return None


def is_unit_available(grade: int, unit_id: str) -> bool:
    return get_unit(grade, unit_id) is not None
