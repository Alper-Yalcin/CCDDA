# Çocuk Çizimlerinden Duygu Sınıflandırması İçin Klinik Özellik Tabanlı Literatür İncelemesi

Bu derleme, çocuk çizimlerinin klinik yorumuna ilişkin klasik projektif literatür ile çağdaş bilgisayarlı görü ve derin öğrenme çalışmalarını birlikte okuyarak hazırlanmıştır. En güvenli ana sonuç şudur: çizimden türetilmiş klinik özellikler **tek başına tanı koydurucu belirteçler gibi değil**, yaşa ve görev tipine göre normalize edilmiş, multimodal ağ içinde düşük-orta ağırlıklı **açıklanabilir yardımcı özellikler** olarak kullanılmalıdır. Bunun nedeni, insan figürü çizimi alanındaki eleştirel derlemelerin çizimlerin tek başına sınırlı güvenirlik ve özgüllüğe sahip olduğunu vurgulaması; buna karşılık sistematik incelemelerin küçük/sadeleştirilmiş çizim, eksiltme, bozulma, gölgeleme ve çizgi süreksizliği gibi bazı biçimsel özelliklerin yine de anlamlı klinik sinyal taşıyabildiğini göstermesidir. HTP’nin geçerliliğini derin öğrenmeyle sınayan 2022 çalışması da bütüncül çizimden depresyonu güvenilir biçimde çıkaramadığı için, sizin kullanım senaryonuz açısından en savunulabilir mühendislik stratejisi, el yapımı klinik özellikleri **soft prior** ve açıklanabilirlik katmanı olarak ağa eklemektir. citeturn24search0turn35search0turn25search0turn14view0turn4view2

## Klinik çizim metrikleri ve bilgisayarlı görü uyarlaması

- **Boyut ve oranlar.** Klasik DAP/HTP yorumunda çok küçük figürler çekilme, yetersizlik, çekingenlik ve düşük öz-yatırım ile ilişkilendirilmiştir; çağdaş meta-analizde de *small drawing size*, *very small house/tree/person* ve *simplified drawing* ruhsal bozukluklarla anlamlı biçimde ilişkili bulunmuştur. Ayrıca nicel ağaç-çizim çalışmalarında depresyon grubunda özellikle *canopy area*, *canopy height*, *canopy width*, *trunk width* ve *total area* daha düşük bulunmuştur. Bunun OpenCV karşılığı doğrudan ölçülebilirdir: `foreground_area / canvas_area`, `bounding_box_area / canvas_area`, `convex_hull_area / canvas_area`, `person_height / canvas_height`, `head_area / person_area`, `tree_area / canvas_area`. Uygulamada gri-seviye ya da HSV uzayında kâğıt-zemin ayrımı yapıldıktan sonra adaptif eşikleme, bağlı bileşen analizi, contour area, convex hull ve minimum bounding rectangle ile bu özelliklerin tamamı çıkarılabilir. citeturn14view0turn15view1turn41view0

- **Yerleşim ve konum.** Klasik yorum rehberlerinde alt kenara yakın yerleşim yetersizlik/güven ihtiyacı, üst yarıya yerleşim iyimserlik/fantazi ve belirgin eğim ise dengesizlik olarak okunur; kontrollü deneysel çalışmalar ise duygusal önemin yerleşimi etkileyebildiğini, fakat bu etkinin genellikle zayıf ve kolay maskelenebilir olduğunu göstermektedir. Bu nedenle konum değişkenleri kullanılmalı, fakat “yüksek-ağırlıklı” değil “bağlamsal” özellikler olarak ele alınmalıdır. Pratik metrikler: `centroid_x`, `centroid_y`, `center_x_offset`, `center_y_offset`, `left_mass_ratio`, `right_mass_ratio`, `top_mass_ratio`, `bottom_mass_ratio`, `principal_axis_angle`, `slant_abs_deg`, `relative_size_to_environment`. OpenCV’de görüntü momentleri ile ağırlık merkezi, PCA ya da en büyük özvektör ile ana eksen, quadrant-occupancy ile sol/sağ-alt/üst kütle dağılımı rahatlıkla hesaplanabilir. Sol-sağ yön yorumları için kanıt dikey yerleşimden daha zayıf olduğundan, `left/right` değişkenleri keşifsel tutulmalıdır. citeturn10view0turn42search1turn35search0

- **Çizgi niteliği ve basınç vekili.** Klinik literatürde “line strength” ve çizgi ağırlığı uzun süredir kullanılmış olsa da, modern bulgular karışıktır: HTP meta-analizi *weak or intermittent lines*, *scribbled drawing*, *shaded or blackened drawing* ve hatta *emphasis on straight lines* gibi biçimsel çizgi özelliklerinin anlamlı sinyal taşıyabildiğini gösterirken, klasik “line heaviness = distress” varsayımı için daha olumsuz kanıtlar da vardır. Bu yüzden taranmış kâğıt çizimlerde “basınç”ı gerçek fiziksel kuvvet gibi değil, **koyu yoğunluk + üst üste binme + stroke kalınlığı + süreksizlik** bileşimi gibi modellemek daha doğrudur. Önerilen metrikler: `stroke_darkness_mean`, `stroke_darkness_std`, `stroke_width_mean`, `stroke_width_std`, `stroke_fragmentation`, `connected_component_count`, `skeleton_break_count`, `straight_line_ratio`, `sharp_angle_ratio`, `shading_ratio`. OpenCV tarafında skeletonization, distance transform, connected components, HoughLinesP ve contour corner sayımı pratik olarak yeterlidir. citeturn16view0turn16view1turn34search1turn37search0

- **Renk psikolojisi.** Çocuklar parlak renkleri daha olumlu, koyu renkleri daha olumsuz duygularla ilişkilendirme eğilimindedir; deneysel çalışmalarda da pozitif/negatif duygusal karakterizasyonlar hem renk kullanımını hem de boyutu sistematik biçimde değiştirebilmiştir. Ancak spontane çizimlerde çocukların çoğu yine de çoğunlukla sevdikleri renkleri kullandığından, klinisyenlerin renk yorumunda “aşırı dikkatli” olması gerektiği özellikle gösterilmiştir. Bu nedenle renk, modelde **dağılımsal ve düşük-ağırlıklı** bir blok olmalıdır; tekil “kırmızı = öfke” ya da “siyah = korku” gibi sert kurallar savunulabilir değildir. Ölçülebilir metrikler: `HSV histogram`, `sat_mean`, `val_mean`, `warm_color_ratio`, `cool_color_ratio`, `dark_color_ratio`, `black_pixel_ratio`, `red_pixel_ratio`, `blue_pixel_ratio`, `achromatic_ratio`, `hue_entropy`, `unique_hue_count`, `no_color_flag`. Önerilen kaba HSV kuralları: sıcak renkler için kırmızı-turuncu-sarı bantları, koyu renk için düşük `V`, renksizlik için düşük `S`. citeturn26view3turn26view2turn29view0turn43view0

- **Eksiltmeler ve distorsiyonlar.** Sayısallaştırılabilir klinik özellikler içinde en güçlü bloklardan biri budur. 2023 HTP meta-analizi *incomplete person*, *loss of facial features*, *poker face*, *inappropriate body proportions*, *single line limbs*, *complete or partial loss of limbs*, *fist*, *negative expression* ve *shaded/blackened person* gibi kişi-çizimi göstergelerinin anlamlı yordayıcılar olduğunu göstermiştir. Koppitz-temelli çocuk çalışmalarında ise `slanted figure`, `shading of face/body`, `feet pressed together`, `omission of eyes`, `tiny figure`, `short arms`, `omission of nose/mouth`, `teeth`, `long arms`, `big hands` gibi daha ayrıntılı alt işaretler kaygı, çekingenlik ve öfke kümelerinde sınıflanmıştır. CV karşılığı, çizimde insan figürünü ve parçalarını bulmaktır: `face_feature_count`, `eye_missing_flag`, `nose_missing_flag`, `mouth_missing_flag`, `hand_missing_flag`, `feet_missing_flag`, `limb_missing_count`, `left_right_arm_asymmetry`, `left_right_leg_asymmetry`, `head_body_ratio`, `fist_prob`, `teeth_prob`, `smile_curve_score`. Saf OpenCV ile contour ve symmetry tabanlı kaba ölçümler üretilebilir; ancak göz, ağız, el ve yumruk gibi özellikler için çizimlere uyarlanmış bir **sketch keypoint/detection** modeli, doğrudan MediaPipe’dan daha gerçekçidir. DAP/HTP otomatik puanlama ve nesne/öğe çıkarımı çalışmalarının varlığı da böyle bir hibrit yaklaşımın teknik olarak uygulanabilir olduğunu göstermektedir. citeturn15view2turn16view2turn16view3turn22view3turn21view1turn6view1turn6view0

Bu bölümden çıkan pratik sınıflama ilkesi şudur: **yüksek güvenli özellikler** boyut, alan, çizgi süreksizliği, gölgeleme/blackening, eksiltme, orantısızlık ve çevreye göre göreli büyüklük; **orta güvenli özellikler** eğim, simetri, açısallık ve yerleşim; **düşük güvenli özellikler** ise tekil renk semantiği, taranmış kâğıttan “gerçek basınç” çıkarımı ve bağlamdan bağımsız sembolik yorumlardır. citeturn14view0turn26view2turn34search1turn35search0

## Dört temel duygu için matematiksel klinik profiller

Aşağıdaki profiller, çocuk çizimi duygu-ifade araştırmaları ile projektif klinik literatürü birleştiren **olasılıksal öncül profiller** olarak okunmalıdır. Bunlar “kesin tanı kuralları” değildir; her biri, multimodal modelinize aktarılacak bir **prior score** için çekirdek özellik kümesidir. Özellikle mutluluk için doğrudan klinik projektif kanıt, üzüntü/anksiyete/öfke kadar geniş değildir; bu nedenle mutluluk profili daha çok “pozitif valans + düşük distres” örüntüsü olarak tanımlanmalıdır. citeturn24search0turn35search0turn29view0turn14view0

- **Mutluluk.** Beklenen en makul profil; orta-büyük çizim alanı, merkez ya da hafif üst-orta dengeli yerleşim, korunmuş yüz ve beden parçaları, düşük eksiltme oranı, düşük stroke fragmentasyonu, gülümseyen/pozitif yüz metriği ve daha parlak/doygun/çeşitli renk dağılımıdır. Deneysel çocuk araştırmalarında “happy” figürler “sad” ve nötr figürlerden daha büyük çizilmiş; düşük anksiyete bağlamlarında çocuklar kişiyi daha bağımsız pozisyonda, gülümser ve çevreyle kıyaslanabilir boyutta çizmiştir. Renk bloğunda parlak ve tercih edilen renkler yardımcı olabilir; fakat bu özellik tek başına belirleyici olmamalıdır. Dolayısıyla mutluluk için çekirdek CV vektörü: `large_area + balanced_center + intact_face + smile_curve + moderate_high_sat_val + high_color_entropy - omissions - fragmentation`. citeturn43view0turn29view0turn44view0turn26view3turn26view2

- **Üzüntü.** En güçlü beklenen örüntü küçük/çok küçük çizim, hareketin yokluğu, sadeleştirme, ek süsleme azlığı, daha düşük ağaç/person alanı, düşük enerji izlenimi, nötr ya da olumsuz yüz ifadesi ve çizgi süreksizliğidir. Affective-disorder literatüründe *no motion* belirgin bir duygudurum göstergesi olarak öne çıkmış; meta-analizde küçük çizim, sadeleştirme ve düşük dekorasyon ortak göstergeler arasında yer almıştır. Nicel ağaç-çizim çalışmalarında depresyon grubunda canopy ve toplam alan küçülmüştür. Renk açısından düşük parlaklık, achromatic kullanım ve düşük çeşitlilik yararlı olabilir; ancak bu blok, renk yorumundaki metodolojik çekince nedeniyle yardımcı blok olarak kalmalıdır. Üzüntü için çekirdek vektör: `small_size + no_motion + simplified + low_decoration + non_smile_or_poker_face + weak_lines + low_color_diversity`. citeturn14view0turn15view1turn41view0turn29view0turn26view2

- **Öfke.** Anger/aggresiveness için en ayırıcı profil yüksek çizgi yoğunluğu, koyu gölgeleme/blackening, açısallık/sert doğrusal konturlar, negatif ifade, yumruk, büyük eller, uzun kollar ve dişlerin vurgulanmasıdır. 2023 HTP meta-analizinde *fist*, *negative expression*, *shaded/blackened person* ve açıklayıcı düzeyde *straight-line emphasis* ile *sharp branch* öfke/çatışma ekseninde önemli görünmektedir; Koppitz-temelli okul öncesi tablolarında da çapraz göz, diş, uzun kol ve büyük el doğrudan anger-aggressiveness kategorisine yerleştirilmiştir. Kırmızı/siyah oranları yardımcı olabilir, fakat bunlar ancak düşük güvenli yan özellik olarak kullanılmalıdır; bağlamı olmayan sert renk kuralları önerilmez. Öfke için çekirdek vektör: `shading_ratio + stroke_darkness + sharp_angle_ratio + straight_line_ratio + fist_prob + big_hand_proxy + long_arm_ratio + teeth_prob + negative_expression_prob`. citeturn16view1turn16view2turn16view3turn21view1turn10view0

- **Korku.** Korku için literatürdeki en yakın klinik karşılık, kaygı/anksiyete örüntüsüdür. Beklenen profil; parçalı ve zayıf/süreksiz çizgiler, eğilmiş/slanted figür, göz-ağız gibi yüz parçalarının eksilmesi, yüz/beden gölgelemesi, ayakların bitişik/sıkışık çizilmesi, figürün çevreye göre küçük kalması, bağımlı duruş ve gülümsemenin yokluğudur. Koppitz-temelli çocuk tablolarında yüz-vücut gölgelemesi, omisyonlar, ayakların bitişik oluşu, bulut/yağmur/kuş gibi tehdit/gerginlik bağlamı veren öğeler anksiyete kategorisinde kodlanmıştır; tehdit uyandıran konuların daha küçük çizilebildiği deneysel olarak da gösterilmiştir. Hastane-anlamlı çizimlerde daha anksiyöz çocuklar kişiyi daha küçük, daha bağımlı ve gülümsemesiz çizmiştir. Korku için çekirdek vektör: `fragmentation + weak_line_ratio + slant_abs_deg + eye_mouth_omission + shading_ratio + feet_pressed_proxy + person_env_size_ratio_small + non_smile + threat_symbol_count`. citeturn22view3turn37search0turn32search24turn44view0

Dört sınıfı birbirinden ayırmak için en yararlı ayrım ekseni, valans kadar **uyarılma biçimi**dir: üzüntü daha çok **küçülme + düşük hareket + sadeleşme**, öfke daha çok **yoğunlaşma + açısallık + abartılmış ekstremiteler**, korku daha çok **parçalanma + eksiltme + eğim + bağımlı küçülme**, mutluluk ise **bütünlük + denge + görece büyük boyut + korunmuş yüz özellikleri** ile temsil edilmelidir. Bu ayrım, el yapımı klinik vektörün sinir ağında neden yararlı olacağını açıklayan en kuvvetli kavramsal çerçevedir. citeturn14view0turn43view0turn44view0turn29view0

## Algoritmik özellik vektörü tasarımı

Pratikte önerim, tek bir düz vektör değil, **dört bloktan oluşan normalize bir klinik vektör + geçerlilik maskesi** kullanmanızdır. Sürekli değişkenler yaş ve görev tipine göre z-skoruna çevrilmeli; eksiltme türü özellikler 0/1 tutulmalı; algılayıcının kararsız olduğu parça özellikleri için ayrıca `validity_mask` geçirilmelidir. Çizimlere uyarlanmış nesne/anahtar-nokta çıkarımının teknik olarak uygulanabilir olduğu DAP/HTP otomasyonu ve çizim-nesne algılama çalışmaları ile; nicel ağaç-çizim indekslerinin bilgisayarlı olarak üretildiğini gösteren depresyon çalışmaları bu tasarımı desteklemektedir. citeturn41view0turn6view0turn6view1

```python
feature_vector = [
    # global kompozisyon
    fg_area_ratio,                 # önplan / tuval
    drawing_bbox_area_ratio,       # çizim bbox / tuval
    drawing_hull_area_ratio,       # convex hull / tuval
    blank_space_ratio,             # boş alan / tuval
    occupied_quadrant_count,       # kaç çeyrek bölgede kütle var
    centroid_x_norm,               # [-1, 1]
    centroid_y_norm,               # [-1, 1]
    left_mass_ratio,
    right_mass_ratio,
    top_mass_ratio,
    bottom_mass_ratio,
    principal_axis_angle_deg,      # ana eksen
    slant_abs_deg,                 # mutlak eğim
    object_count,                  # house/tree/person/diğer büyük objeler
    mean_interobject_distance_norm,

    # kişi / oran / asimetri
    person_area_ratio,
    person_height_ratio,
    person_env_size_ratio,         # kişi / çevre objeleri
    head_body_ratio,
    shoulder_body_ratio,
    arm_length_left_norm,
    arm_length_right_norm,
    arm_asymmetry,
    leg_length_left_norm,
    leg_length_right_norm,
    leg_asymmetry,
    hand_area_ratio,
    face_feature_count,
    eye_missing_flag,
    nose_missing_flag,
    mouth_missing_flag,
    hand_missing_flag,
    feet_missing_flag,
    limb_missing_count,
    fist_prob,
    teeth_prob,
    smile_curve_score,
    negative_expression_prob,
    no_motion_flag,

    # çizgi / basınç vekili
    stroke_darkness_mean,
    stroke_darkness_std,
    stroke_width_mean,
    stroke_width_std,
    stroke_fragmentation,
    connected_component_count_norm,
    skeleton_length_norm,
    skeleton_break_count_norm,
    straight_line_ratio,
    sharp_angle_ratio,
    curve_entropy,
    shading_ratio,
    weak_line_ratio,

    # renk
    hsv_hue_entropy,
    sat_mean,
    val_mean,
    warm_color_ratio,
    cool_color_ratio,
    dark_color_ratio,
    black_pixel_ratio,
    red_pixel_ratio,
    blue_pixel_ratio,
    achromatic_ratio,
    color_diversity_count,
    no_color_flag,
]
```

Bu vektörün en “yük taşıyan” çekirdek altkümesi şunlardır: `fg_area_ratio`, `centroid_y_norm`, `stroke_darkness_mean`, `stroke_fragmentation`, `sharp_angle_ratio`, `shading_ratio`, `warm_color_ratio`, `dark_color_ratio`, `color_diversity_count`, `face_feature_count`, `mouth_missing_flag`, `hand_missing_flag`, `arm_asymmetry`, `fist_prob`, `smile_curve_score`, `no_motion_flag`. Eğer ilk sürümde bütçeyi düşürmek isterseniz, modeli önce bu çekirdek altküme ile kurup daha sonra tam vektöre genişletmeniz daha kontrollü olacaktır.

Neuro-symbolic katman için bu vektörden dört yumuşak öncül skor türetilebilir:

```python
sadness_prior   = sigmoid(+small_size + no_motion + simplified + weak_lines
                          + non_smile + low_color_diversity + dark_or_achromatic)

anger_prior     = sigmoid(+shading + stroke_darkness + angularity + straightness
                          + fist_prob + big_hand_proxy + long_arm_ratio + teeth_prob)

fear_prior      = sigmoid(+fragmentation + slant + eye_mouth_omission + shading
                          + small_vs_environment + dependent_pose_proxy + threat_symbols)

happiness_prior = sigmoid(+balanced_center + larger_area + intact_face + smile
                          + moderate_high_sat_val + color_diversity
                          - fragmentation - omissions - heavy_shading)
```

Bu skorların **hard rule** olarak değil, `clinical_branch = MLP([feature_vector, validity_mask, age_months, task_id])` girişine eşlik eden yumuşak öncüller olarak kullanılması daha doğrudur. Özellikle yaş normalizasyonu zorunludur; çünkü beden parçalarının görülmesi ve ince motor üretim 5–9 yaşta hızla değişmektedir, dolayısıyla “omitted hands” ya da “missing neck” gibi işaretler yaş kontrolü olmadan yanlış-pozitif üretebilir. citeturn20view0turn22view3

Bir başka kritik mühendislik noktası, **metinle koşullandırılmış özellik ağırlığı** kullanmaktır. Örneğin `black_pixel_ratio` yüksek ama açıklamada “gece”, “saç”, “takım elbise”, “yağmurlu hava” gibi nesnel bağlam varsa, siyah oranının klinik ağırlığı otomatik düşürülmelidir; aynı şekilde “rain/cloud” sembolleri anksiyete işareti gibi kodlanmadan önce açıklamadaki bağlamla kontrol edilmelidir. Bu, klinik literatürde tekil işaretlerin bağlama duyarlı ve kimi zaman yanıltıcı olabileceğini gösteren bulgularla tam uyumludur. citeturn26view2turn10view0turn45search13

## Akademik kaynakça

Aşağıdaki liste, hem klinik projektif çizim literatürünü hem de sayısallaştırma/otomasyon literatürünü birlikte içerir. Son yıllardaki bazı çalışmalar çocuk dışı ya da ergen/erişkin örneklem de içerse bile, onları özellikle **nicel ölçülebilirlik**, **otomatik puanlama** ve **karşı-delil** sağladıkları için dahil etmek gerekir.

- *Emotional indicators on human figure drawings of children: a validation study* — **entity["people","E. M. Koppitz","human figure test author"]** (1966). İnsan figürü çizimlerinde duygusal göstergeler sisteminin erken doğrulama makalesidir; HFD’deki bazı işaretlerin klinik ayrım yapabileceği tezini başlatan temel kaynaktır. citeturn23search3

- *Emotional indicators on human figure drawings of shy and aggressive children* — E. M. Koppitz (1966). Tek tek göstergelerin bire bir duygusal karşılık vermediğini, ancak bazı işaret kümelerinin utangaç ve saldırgan çocuk gruplarında daha sık görüldüğünü gösteren klasik karşılaştırmalı çalışmadır. citeturn45search1turn45search13

- *Human figure drawings as a measure of children’s emotional status: critical review for practice* — **entity["people","Theresa Skybo","pediatric nursing scholar"]** ve ark. (2007). Uygulama açısından en önemli kritik derlemelerden biridir; çizimlerin yararlı olabileceğini, ancak yorumun dikkatli ve sınırlı yapılması gerektiğini savunur. citeturn24search0turn24search4

- *Drawing conclusions: A re-examination of empirical and conceptual bases for psychological evaluation of children from their drawings* — **entity["people","Glyn V. Thomas","child drawing researcher"]** ve **entity["people","Richard P. Jolley","drawing psychology scholar"]** (1998). Çizimlerin tek başına çok anlamlı ve güvenilir bir kişilik/duygudurum göstergesi olmadığını; varsa bile etkilerin küçük ve bağlama duyarlı olduğunu gösteren kavramsal-eleştirel çalışmadır. citeturn35search0turn35search3

- *Effects of different emotion terms on the size and colour of children’s drawings* — **entity["people","Esther Burkitt","developmental psychologist"]** ve ark. (2009). “Happy” ve “sad” gibi farklı duygusal etiketlerin çocukların çizim boyutunu ve renk kullanımını sistematik olarak değiştirdiğini gösterir; duyguya duyarlı ölçülebilir çizim göstergeleri için çok değerlidir. citeturn29view0

- *Does Children’s Colour Use Reflect the Emotional Content of their Drawings?* — **entity["people","Emily Crawford","developmental psychology author"]** ve ark. (2011). Renk yorumunda aşırı temkin gerektirdiğini gösterir; çocuklar olumsuz içerikli spontane çizimlerde bile çoğu zaman sevdikleri renkleri kullanmaya devam eder. citeturn26view2

- *Children’s emotional associations with colors* — **entity["people","C. J. Boyatzis","color emotion researcher"]** ve **entity["people","R. Varghese","psychology coauthor"]** (1994). Parlak renklerin daha olumlu, koyu renklerin daha olumsuz duygularla eşleştirildiğini deneysel olarak gösterir; `bright/dark ratio` gibi özelliklerin neden yalnızca yardımcı blok olması gerektiğini de açıklar. citeturn26view3

- *Analysis of the screening and predicting characteristics of the house-tree-person drawing test for mental disorders: A systematic review and meta-analysis* — **entity["people","Huibing Guo","psychiatry meta-analysis author"]** ve ark. (2023). Otuz çalışmadan 6295 katılımcıyı birleştirerek 39 anlamlı HTP göstergesi saptar; eksiltme, bozulma, aşırı ayrıntı ve küçük/sade çizim bloklarını sayısallaştırma açısından en güçlü güncel kaynaktır. citeturn14view0turn15view0turn15view1turn15view2turn16view1

- *Screening Depressive Disorders With Tree-Drawing Test* — **entity["people","Simeng Gu","tree drawing researcher"]** ve ark. (2020). Bilgisayarlı görüntü tanıma ile canopy/trunk/root alanlarını nicel olarak çıkarır; beş sayısal ağaç özelliğinin depresyon gruplarını ayırabildiğini gösterir. citeturn41view0

- *Generating psychological analysis tables for children’s drawings using deep learning* — **entity["people","Moonyoung Lee","drawing ai researcher"]** ve ark. (2024). Nesne tespitiyle çizimdeki öğelerin sayı, boyut ve konumlarını çıkarıp psikolojik analiz tablosu üretir; bu, sizin el yapımı klinik vektör fikrinize doğrudan teknik dayanak sağlar. citeturn6view0

- *Two-Step Fine-Tuned Convolutional Neural Networks for Multi-label Classification of Children’s Drawings* — **entity["people","Muhammad Osama Zeeshan","document analysis researcher"]** ve ark. (2021). Draw-a-Person örneklerinde çok etiketli otomatik puanlamanın mümkün olduğunu ve çizimlere uyarlanmış CNN mimarilerinin klasik ön-eğitimli ağlardan daha iyi sonuç verebildiğini gösterir. citeturn6view1

- *The House-Tree-Person test is not valid for the prediction of mental health: An empirical study using deep neural networks* — **entity["people","Yijing Lin","htp validity author"]** ve ark. (2022). Karşı-delil niteliğindedir; DNN’lerin HTP çizimlerinden depresyonu güvenilir biçimde çıkaramadığını göstererek projektif çizim özelliklerinin yardımcı/olasılıksal kullanılmasını destekler. citeturn4view2

- *Evaluating the Tree Drawing Test Depression Assessment Scale for adolescent depression screening* — **entity["people","Guorui Liu","tree drawing scale author"]** ve ark. (2025). Bilgisayarlı görüntü tanıma destekli ağaç-çizim ölçeğinin ergen depresyon taramasında iyi özgüllük, duyarlılık ve rater uyumu verdiğini gösterir; yeni kuşak klinik karar destek sistemleri için önemlidir. citeturn14view3