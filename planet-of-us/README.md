# PLANET OF US

> Tüm dünyanın birlikte yaşattığı tek bir gezegen. Yorumuna bayrağını bırakan herkes bir ülkenin vatandaşı.
> Ülkeler büyümek için yarışır ama gezegeni ancak hep birlikte kurtarabilirler.

Bu klasör kanal konseptini ve **çalışan bir prototipi** içerir. Prototip, sahte istatistiklerle simüle edilmiş 7 günden 7 dikey Shorts videosu üretir.

- Önizleme videosu (sesli, dönen 3D gezegen, 720x1280): [`preview/week.mp4`](preview/week.mp4)
- 7 günün son kareleri: [`preview/sheet.png`](preview/sheet.png)
- Günlük olay kaydı: [`preview/log.md`](preview/log.md)

---

## 1. Fikir tek cümlede

Kanalda bir gezegen yaşar. Gezegeni her gün **bir önceki videonun izlenmesi, beğenisi ve yorumları** şekillendirir. Yorumdaki bayrak emojisi o ülkeye oy demektir. Ülkeler boş topraklara yayılır. Ara sıra bir asteroit ya da salgın gelir; ertesi gün **toplam yorum sayısı** hedefe ulaşmazsa gezegen zarar görür. Gezegenin sağlığı sıfıra inerse **gezegen ölür ve bu geri alınamaz**.

## 2. "Kanal canlı" fikrinden farkı

| İstek | Önceki fikir: tek yaratık | PLANET OF US |
|---|---|---|
| **Evrensel** | Yaratık kimseye ait değil | Dünyanın her ülkesi haritada; herkes kendi bayrağını görür |
| **Toplumsal** | Bireysel bakım | Ülkeler hem yarışır hem tehditlere karşı birlikte savaşır; insanlığın küçük bir aynası |
| **Heyecanlı** | Yavaş ilerleyen bir hikaye | Her gün sıralama değişir; asteroit uyarıları, ilk temaslar, anıtlar |
| **Viral motor** | Acıma duygusu | **Ulusal gurur**: "Türkiye 6. sıraya düştü, 🇹🇷 yaz!" Paylaşım kendiliğinden gelir |
| **Verimli** | Karakter animasyonu gerekir | Tamamen kodla üretilir; her gün otomatik render, insan işi yaklaşık 5 dakika |

## 3. Kurallar (prototipte çalışan hali)

| Girdi (dünkü video) | Gezegende karşılığı |
|---|---|
| İzlenme | **Güneş ışığı**: bütün ülkelerin büyüme hızı (logaritmik) |
| Beğeni | **Sağlık**: beğeniler iyileştirir, her gün sabit bir kayıp olur |
| Yorumdaki bayrak 🇧🇷 | O ülkeye **1 oy**. Oy sayısı arttıkça toprak büyür (karekök ölçekli, kalabalık ülkeler ezip geçmesin diye) |
| İlk kez görülen bayrak | **Yeni ülke** gezegene iner. Başlangıç noktası diğerlerinden en uzak boş alan seçilir |
| İki ülkenin sınırlarının değmesi | **İlk temas**: ticaret yolu açılır, ikisi de kalıcı büyüme bonusu alır |
| En çok beğenilen yorum | Yorumu yazanın ülkesinde **anıt** olarak gezegene kazınır |
| Tehdit uyarısı | Ertesi gün N toplam yorum gelmezse çarpma olur: toprak kaybı, sağlık -20, anıtlar yok olur |
| Sağlık = 0 | **Gezegen ölür.** Sezon finali ve yeni gezegen |

**Ülkeler birbirine saldıramaz.** Bu bilinçli bir tasarım kararı. Gerçek çatışmaların yorumlara taşınmasını engeller, rekabeti "boş toprağa kim önce ulaşır" yarışına çevirir.

## 4. İçerik planı

- **Her gün bir Shorts (8–15 sn):** Günün haritası, sıralama değişimi, olay başlıkları, yarının tehdidi. Tamamen otomatik.
- **Haftalık özet (8–12 dk, uzun video):** Haftanın hikayesi; kim yükseldi, kim çöktü, hangi yorum anıt oldu. YPP için gereken izlenme saatini bu videolar toplar. Anlatımı Claude yazar.
- **Sezon finali:** Gezegen ölürse ya da 100 güne ulaşırsa "Bir gezegenin tüm tarihi" belgeseli. En çok paylaşılacak video bu olur.

## 5. Büyüme döngüsü

1. Bir kişi kendi ülkesinin geride olduğunu görür.
2. Bayrağıyla yorum yazar ve videoyu yurttaşlarına gönderir.
3. Ülkesi büyür. Diğer ülkeler bunu görüp karşılık verir.
4. Tehdit gelir. Bütün ülkeler birbirini yorum yazmaya çağırır.
5. Gezegen kurtulursa kutlama, kurtulmazsa "suçlu kim?" tartışması. İki durumda da etkileşim artar.

Bunun sonucunda **izleyiciler kanalın pazarlamasını kendileri yapar.** Yazarın "minimal pazarlama" şartı burada karşılanıyor.

## 6. Gelir

1. **AdSense:** Global ve karışık bir kitle olduğu için RPM düşük olur. Asıl gelir uzun özet videolardan gelir.
2. **Kanal üyeliği:** Üyelerin ülkesine haftalık bonus ya da özel anıt hakkı. **Dikkat:** Para karşılığı oyunda avantaj vermek eleştirilebilir, ayrıca YouTube kurallarına uygunluğu kontrol edilmeli.
3. **Canlı yayın (ileri aşama):** Gezegen 7/24 canlı akar, Super Chat ile anlık olaylar tetiklenir.
4. **Ürün:** Sezon sonunda gezegenin son halinin poster versiyonu (Etsy ödeme sorununu da çözer).

## 7. Riskler ve önlemler

| Risk | Önlem |
|---|---|
| **Sıfırdan başlama:** İlk gün kimse yok | İlk 7 gün tehdit yok, eşikler düşük. İlk Shorts'ta bütün kuralları anlatan "trailer" |
| **YouTube "engagement bait" sayabilir** | Mekanik şeffaf anlatılır, ödül vaadi yok, sahte aciliyet yok. YouTube'un spam ve yanıltıcı uygulamalar politikası yayından önce okunmalı (henüz kontrol edilmedi) |
| **Milliyetçi kavga ve nefret yorumları** | Saldırı mekaniği yok. Anıtlar filtreli. Yorum moderasyonu için YouTube'un engellenen kelimeler listesi kullanılır. Tehditler işbirliğini ödüllendirir |
| **Bot ve spam yorumlar** | Aynı kullanıcının aynı gündeki oyu tek sayılır (API ile yazar kimliği alınabilir). Prototipte henüz yok |
| **Büyük ülkeler her zaman kazanır** | Karekök ölçek + yeni ülkeye uzak başlangıç + ticaret bonusu. Gerekirse küçük ülkelere "underdog" bonusu |
| **Sıkıcılaşma** | Mevsimler, nadir olaylar (kuyruklu yıldız, altın çağ), sezon sonları |
| **Gerçek ülke adları siyasi hassasiyet** | Bayraklar sadece kimlik işareti. Sınırlar ve olaylar tamamen kurgusal; çatışma yok |

## 8. Teknik yapı

```
planet-of-us/
├── planet/
│   ├── sim.py        # dünya motoru: kurallar, büyüme, tehditler, anıtlar
│   ├── render.py     # bir günü 540x960 dikey videoya çevirir (Pillow + ffmpeg)
│   └── fake_data.py  # YouTube API gelene kadar sahte "dünkü istatistikler"
├── run_demo.py       # 7 günlük demo: out/dayN.mp4, out/week.mp4, out/log.md, out/sheet.png
└── preview/          # repoya eklenmiş demo çıktıları
```

Gereksinimler: Python 3.10+, Pillow, ffmpeg. Başka paket yok.

```bash
cd planet-of-us
python3 run_demo.py
```

## 9. Yol haritası

- [x] Dünya motoru + günlük render (prototip)
- [x] Ses: prosedürel ambiyans + olay efektleri (pop, çan, alarm, çarpma)
- [x] Dönen 3D gezegen: ışık, bulutlar, atmosfer, gece tarafında şehir ışıkları, asteroit efekti
- [ ] `youtube_stats.py`: YouTube Data API ile dünkü videonun izlenme, beğeni ve yorumları; yazar başına tek oy
- [ ] Durum kalıcılığı: `state.json` (dünya her gün kaldığı yerden devam eder)
- [ ] Haftalık özet videosu üreticisi (16:9, anlatım metni + grafikler)
- [ ] Yükleme: başta elle. API ile otomatik yüklemede, denetlenmemiş projelerin videoları gizli kalabiliyor; bu kontrol edilmeli
- [ ] İlk 30 Shorts'luk lansman takvimi

## 10. Doğrulanmamış varsayımlar

- Bu formatı düzenli yapan bir YouTube kanalı olmadığı varsayımı **araştırılmadı**.
- YouTube'un yorum isteme mekaniklerine bakışı **kontrol edilmedi**.
- Demo sayıları (izlenme, yorum) tamamen **uydurma**. Gerçek bir kanalın ilk haftası çok daha düşük olur.
