# CCDDA

Eski multimodal AI hatti bu repodan temizlendi.

Kaldirilan eski yapi:
- emotion + gender cok-gorevli siniflandirma
- text/BERT tabanli multimodal akis
- eski checkpoint, explainability ve inference kodlari

Mevcut durum:
- repo yeni etiketli image-only veriyle sifirdan kurulacak yeni AI sistemi icin hazirlaniyor
- legacy AI giris noktalari bilincli olarak devre disi birakildi
- `api_server.py` calissa bile `/predict` su anda `503 reset_in_progress` doner

Korunan genel parcalar:
- proje iskeleti
- web/desktop kabugu
- genel goruntu transform yardimcilari
- dokumantasyon ve rapor dosyalari

Bir sonraki asamada kurulacak yeni sistem icin cekirdekler:
- yeni veri manifest uretimi
- 4 sinifli image-only egitim hatti
- yeni model mimarisi
- klinik/CV ozellik cikarim katmani