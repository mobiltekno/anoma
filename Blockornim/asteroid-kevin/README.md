# Asteroid Kevin

Dünya'ya doğru gelen, yorgun ve ironik bir asteroit. İzleyici yorumlarına Shorts ile cevap veriyor, yorumların havasına göre hızlanıyor ya da yavaşlıyor. Sezon finalinde çarpıp çarpmayacağına yorumların toplamı karar veriyor.

## 1. Ses testi (`voice-tests/`)

Tüm örnekler aynı replikle üretildi:

> "Day forty seven. Two point three million kilometers to Earth. Yesterday, humans defended pineapple on pizza. Noted. Mehmet from Turkey writes: Kevin, please spare us, we have cats. … Okay. Cats are fine. I'm slowing down. Fifty thousand kilometers. But John from the UK called me a potato. … I'm speeding up."

| Dosya | Motor / ses | İşlem |
|---|---|---|
| `01_kevin-fx_kokoro_am_adam` | Kokoro, Amerikan, derin | Kevin efekti |
| `02_kevin-fx_kokoro_am_onyx` | Kokoro, Amerikan, kalın | Kevin efekti |
| `03_kevin-fx_kokoro_bm_lewis` | Kokoro, İngiliz | Kevin efekti |
| `04_kevin-fx_kokoro_am_fenrir` | Kokoro, Amerikan | Kevin efekti |
| `05_kevin-fx_kokoro_bm_george` | Kokoro, İngiliz, olgun | Kevin efekti |
| `06_kevin-fx_piper_en_US-ryan-high` | Piper, Amerikan | Kevin efekti |
| `07_raw_kokoro_am_adam` | Kokoro, efektsiz | Karşılaştırma için |
| `08_raw_piper_en_GB-alan-medium` | Piper, efektsiz | Karşılaştırma için |

**"Kevin efekti":** Ses yaklaşık 2 yarım ton kalınlaştırılıyor (süre değişmiyor), bas güçlendiriliyor, sıkıştırılıyor ve hafif bir "uzay" yankısı ekleniyor. Komut `ffmpeg -af "asetrate=24000*0.88,aresample=24000,atempo=1/0.88,bass=g=4:f=110,acompressor=threshold=-18dB:ratio=3,aecho=0.8:0.5:60|140:0.18|0.10,loudnorm=I=-16"`.

**Anlaşılırlık kontrolü:** Whisper ile yazıya dökülen metin, orijinal metnin kelimelerinin %74–84'ünü yakaladı. Kaçırılanlar çoğunlukla "Mehmet" ve rakama çevrilen sayılar ("forty seven" → "47"). Yani bütün sesler anlaşılır, aralarındaki fark kalite ve karakter. Seçimi kulakla yapmak gerekiyor.

Lisans: Kokoro-82M Apache 2.0. Piper sesleri için her sesin kendi model kartına bakılmalı (bazıları ticari kullanıma kısıtlı olabilir, kontrol edilmedi).

## 2. YouTube kontrolleri (23 Kasım 2026)

Kaynak: YouTube kanal ve arama sayfaları (ytInitialData). Birkaç istekten sonra YouTube captcha istedi, bu yüzden izleme sayfaları (yaş ve "çocuklara yönelik" durumu) **kontrol edilemedi**.

### SolarBalls (@SolarBalls): 2,29M abone

- **Uzun videolar istikrarlı:** Son 30 videonun her biri 376K–913K izlenmiş. Yaklaşık 8–10 dakika, çoğu "Part 1/2/3" şeklinde **seri hikayeler**.
- **En iyi performans tehdit ve felaket hikayelerinde:** "The Sun vs The Rogue Planets" 2,2M, "The Solar System vs The Rogue Planets" (4 saatlik derleme) 1,3M, "The Moon Killer" serisi, "The Solar Reckoning". Kevin'in hikayesi tam bu temaya oturuyor.
- **Uzun derlemeler ve "film" formatı çalışıyor:** "ASTRODUDE: A SolarBalls Movie" (1 saat) 9 günde 867K. "The Birth of Saturn's Rings" (1 saat 12 dk) 805K.
- **Şarkı:** "The Solar System Song" 2,9M ile en çok izlenen video.

### SolarBalls çevresindeki küçük kanallar (bu yıl)

Hayranların yaptığı "planetballs" animasyonlarından oluşan **aktif bir alt tür** var:

- OneFormerPlanet: "The Solar System's Death (SolarBalls Fan Animation)", 23 sn, 238K izlenme
- Imitater: "The Solar System History… #solarballs", 18 sn, 548K izlenme
- SolarSpheres: 3D, 527K izlenme
- Yuvelev: 2 saatlik planetballs zaman çizelgesi, 50K izlenme
- Beyond the Observable Universe: 15–20 saniyelik bilgi Shorts'ları, 130K–1,3M izlenme

**Düzeltme:** Önceki raporda "kopya dalgası yok" demiştim. Bu yanlış. Küçük ama aktif bir hayran animasyonu ekosistemi var. Bu hem talebin canlı olduğunu gösteriyor hem de rekabetin sanıldığından fazla olduğunu.

### "Asteroid animation funny" araması

Sonuçlarda büyük ölçüde **çocuklara yönelik** içerik var: Peppa Pig, PJ Masks, Dr Binocs, Hint çizgi filmleri. Komik, yetişkinlere yönelik bir asteroit karakteri yok.

### "Talking asteroid" araması

Bilim (StarTalk, Cleo Abram) ve haber içerikleri. "How Dinosaurs Talked About The Asteroid Probably" (Siliconversations, 182K) dışında **komik ve konuşan bir asteroit karakteri yok.** Boşluk doğrulandı.

### "Planet comedy animation" (bu yıl)

Çok sayıda düşük performanslı Shorts var. "Plüton gezegenlikten atıldı" esprisi defalarca işlenmiş: 1K–5K izlenme. **Plüton espirisi tükenmiş.** Kevin'in arkadaşı olarak kullanılırsa yeni bir açı bulunmalı.

### "Talking object shorts"

Birkaç büyük hit var (3,3M, 9,4M, 1M), ama yüzlerce video 10–50 izlenmede kalıyor. Format AI video araçlarıyla dolup taşmış. **Tek başına konuşan nesne olmak yetmez,** süreklilik ve karakter gerekiyor.

## 3. Sonuçlar ve pilot için kararlar

1. **Uzun seri hikaye + Shorts.** SolarBalls'un modeli (8–10 dk, 3 bölümlük tehdit hikayeleri, derlemeler) uzun video tarafında iş görüyor. Kevin'in ana motoru yorum cevabı Shorts'ları olacak, ama gelir ve izlenme saati için "Kevin'in yolculuğu" bölümleri de gerekli.
2. **Ton bilinçli olarak 13+.** Asteroit ve gezegen aramalarını çocuk içeriği domine ediyor. Bizim farkımız kara mizah. Bu aynı zamanda "çocuklara yönelik" işaretlenip yorumların kapanması riskini azaltıyor.
3. **Görsel stil SolarBalls'tan ayrı olmalı.** Top gibi gezegenler kullanmayacağız: düzensiz kaya formu, büyük ve yorgun gözler, kendine özgü bir renk paleti. Hayran ekosistemiyle karışmamak için ayırt edici olmak şart.
4. **Plüton yerine yeni yan karakterler** düşünülmeli. Örnek: Kevin'i takip eden, sürekli "selfie" çeken bir uzay sondası, ya da Kevin'e âşık bir kuyruklu yıldız.
