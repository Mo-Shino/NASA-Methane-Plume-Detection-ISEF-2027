# SpectraPlume: Autonomous Spaceborne Methane Radar & Flux Quantification
### Regeneron ISEF 2027 Research Project | Alexandria, Egypt
**Autonomous Super-Emitter Methane Plume Detection & Mass Flux Quantification from NASA EMIT Hyperspectral Satellite Data via Spatial-Spectral Computer Vision & Radiative Transfer Inversion**

[![ISEF 2027](https://img.shields.io/badge/Competition-Regeneron%20ISEF%202027-blue.svg)](https://www.societyforscience.org/isef/)
[![Category](https://img.shields.io/badge/Category-Earth%20%26%20Environmental%20Sciences%20(EAEV)-emerald.svg)](#)
[![Sub-Category](https://img.shields.io/badge/Sub--Category-Atmospheric%20Science%20(AIR)-teal.svg)](#)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![NASA EMIT](https://img.shields.io/badge/Data-NASA%20EMIT%20L2A%2FL2B-orange.svg)](https://earth.jpl.nasa.gov/emit/)

---

## 📌 ملخص المشروع (Project Abstract)

يعتبر غاز الميثان ($\text{CH}_4$) من أخطر الغازات الدفيئة المسؤولة عن تسارع الاحتباس الحراري، حيث تفوق قدرته على حبس الحرارة **84 ضعف ثاني أكسيد الكربون ($\text{CO}_2$)** خلال أول 20 عاماً من انبعاثه. وتصدر النسبة الأكبر من الانبعاثات الكارثية عن تسريبات مجهولة ومفاجئة في البنية التحتية للنفط والغاز (**Super-Emitters** بمعدلات تسريب تتجاوز أطناناً في الساعة).

يقدم مشروع **SpectraPlume** منظومة برمجية وفيزيائية متكاملة ذاتية التشغيل بالرؤية الحاسوبية المكانية-الطيفية (Autonomous Spatial-Spectral Vision Framework) تعمل على:
1. **استقبال ومعالجة بيانات القمر الصناعي فائق الأطياف التابع لناسا (NASA EMIT):** المثبت على محطة الفضاء الدولية (ISS) والذي يمسح الأرض في 285 نطاقاً ضوئياً في الأشعة تحت الحمراء قصيرة الموجة (SWIR).
2. **عزل سحب الميثان الشفافة ذاتياً:** عبر الدمج بين المرشح المطابق الموحد (Unit Matched Filter) وشبكة الانتباه المكاني-الطيفي المسبوقة بتطبيع العمق الضوئي المستمر (Continuum Optical-Depth Normalization).
3. **القضاء على الإنذارات الكاذبة التضاريسية:** التغلب على معضلة تداخل بصمة صخور الكربونات والكالسيت ($2.3\,\mu\text{m}$) والرمال عالية الانعكاس بمعامل **F1 = 0.942** (**Precision 96.1%**, **Recall 92.4%**) وخفض الإنذارات الكاذبة بنسبة **78.4%** عبر 42 مسحاً حقيقياً لقمر ناسا EMIT (وبنسبة كبت **100%** على مشاهد الكالسيت الخالية من الغاز).
4. **التقدير اللحظي لمعدل التسريب الكتلي ($Q \pm \sigma_Q$):** حساب معدل التدفق بالطن/ساعة بنموذج التراكم الكتلي المتكامل (IME) بحد حساسية يصل إلى **85 kg/h** مع دمج سرعات رياح ERA5 ونمذجة هامش الخطأ ومجال الثقة 95%.
5. **إسقاط جغرافي دقيق على صور الأقمار الصناعية (GIS Satellite Imagery):** لتحديد موقع التسريب على خريطة Esri الفضائية وإصدار تقارير طوارئ رقمية معتمدة بصيغة JSON.

---

## 🏛️ الهيكل التنظيمي للمستودع (Repository Structure)

```text
NASA-Methane-Plume-Detection-ISEF-2027/
│
├── 🚀 run_demo.py                    <-- [متعدد الأنظمة] مشغل تلقائي لويندوز وماك ولينكس بدون أي إعداد يدوي
├── 🚀 run_demo.bat                   <-- [ضغطة واحدة لويندوز] تشغيل النظام وفحص الاعتماديات وفتح لوحة التحكم
├── 🌐 app.py                          <-- لوحة التحكم السحابية والمحلية (Streamlit Mission Control Center)
├── ⚙️ pipeline_runner.py              <-- خط المعالجة الهجين المتكامل (Physics + Spatial-Spectral AI Engine)
├── 🧠 train_model.py                  <-- تدريب ومعايرة أوزان شبكة الانتباه المكاني-الطيفي
├── 🐳 Dockerfile                      <-- حاوية جاهزة للنشر السحابي (Hugging Face Spaces / Render / Cloud Run)
├── 📦 requirements.txt               <-- حزم بايثون القياسية المتوافقة مع السيرفرات السحابية
├── 📂 .streamlit/config.toml         <-- إعدادات الثيم الفضائي الداكن وإعدادات السيرفر السحابي
│
├── 📂 src/                            <-- المحركات الفيزيائية والخوارزميات الأساسية
│   ├── benchmark_generator.py         <-- محرك التوليد الذاتي للمشاهد الأربعة وإعادة بناء رحلة ناسا Orbit 2222205
│   ├── data_loader.py                 <-- معالج بيانات ناسا ذاتي الاستشفاء (Self-Healing NetCDF4 Loader)
│   ├── flux_calculator.py             <-- حاسبة التدفق الكتلي (IME) وحساب انتشار الأخطاء (Gaussian)
│   ├── gis_visualizer.py              <-- محرك الخرائط الفضائية التفاعلية (Esri World Imagery)
│   ├── matched_filter.py              <-- المرشح المطابق الطيفي لبصمة الميثان (HITRAN 2024 Doublet)
│   ├── model_spatial_spectral.py      <-- الشبكة العصبية المكانية-الطيفية مع تطبيع العمق الضوئي
│   └── real_granule_fetcher.py        <-- أداة الاستعلام المباشر وتنزيل الـ Granules من سيرفرات ناسا
│
├── 📂 tests/                          <-- الاختبارات العلمية والفيزيائية واختبارات قابلية النقل
│   └── test_physics_and_pipeline.py   <-- 8 اختبارات آلية شاملة (HITRAN, Orbit 2222205, Calcite, IME, Portability)
│
├── 📂 data/                           <-- مجموعات البيانات ومشاهد الأقمار الصناعية
│   ├── benchmark_scenes/              <-- تولد تلقائياً عند أول تشغيل على أي جهاز أو سيرفر
│   └── real_emit/                     <-- بيانات وإحداثيات رحلة ناسا الحقيقية (LP DAAC Plume Complex 485)
│
├── 📂 weights/                        <-- الأوزان العصبية المعايرة للنموذج
│   └── spatial_spectral_emit.pt       <-- أوزان شبكة الـ SpatialSpectralMethaneNet المعايرة
│
├── 📂 docs/                           <-- الوثائق البحثية والمواصفات الفيزيائية وسكريبت التحكيم
└── 📂 display_board/                  <-- لوحة العرض الرسمية لمسابقة ISEF (100x70 سم) والشعارات الفيكتور
```

---

## 🔬 الأسس العلمية والرياضية (Mathematical Formulation)

### 1. المرشح المطابق الطيفي الموحد (Unit-Normalized Matched Filter)
$$\alpha(x) = \frac{(x - \mu)^T \Sigma_{\text{reg}}^{-1} t}{t^T \Sigma_{\text{reg}}^{-1} t}$$
* $x \in \mathbb{R}^B$: طيف الانعكاسية المقاس للبكسل عبر 40 نطاقاً طيفياً في نافذة $2150 - 2450\,\text{nm}$.
* $\mu \in \mathbb{R}^B$: متوسط انعكاسية الخلفية المحلية للمشهد.
* $\Sigma_{\text{reg}} = \Sigma + \lambda I$: مصفوفة التغاير المنظمة مع عامل الاستقرار التكيفي $\lambda = 10^{-4}$.
* $t \in \mathbb{R}^B$: بصمة الامتصاص الجزيئي للميثان وفق قاعدة بيانات **HITRAN 2024** (الامتصاص المزدوج عند $2315\,\text{nm}$ و $2260\,\text{nm}$).
* $\alpha(x)$: كثافة عمود الميثان الزائدة بوحدة $\text{ppm}\cdot\text{m}$.

### 2. نموذج التراكم الكتلي المتكامل (Integrated Mass Enhancement - IME)
$$\text{IME} = \sum_{i \in \text{Plume}} \Delta \Omega_i \cdot A_{\text{pixel}} \cdot k_{\text{CH}_4} \quad [\text{kg}]$$
$$Q = \frac{\text{IME} \cdot U_{\text{eff}}}{L} \times 3600 \quad [\text{kg/hr}]$$
* $A_{\text{pixel}} = 3600\,\text{m}^2$: مساحة البكسل الأرضي لقمر ناسا EMIT ($60\,\text{m} \times 60\,\text{m}$).
* $k_{\text{CH}_4} = 7.16 \times 10^{-7}\,\text{kg/(m}^2 \cdot \text{ppm}\cdot\text{m)}$: ثابت التحويل الكتلي المولي للميثان.
* $U_{\text{eff}}$: سرعة الرياح الفعالة المستخلصة من نماذج إعادة التحليل الأوروبية ERA5.
* $L$: طول السحابة الفعلي على طول محور الانتشار الهيدروديناميكي.

### 3. حساب انتشار الأخطاء ومجال الثقة (Gaussian Error Propagation)
$$\sigma_Q = Q \sqrt{\left(\frac{\sigma_{\text{IME}}}{\text{IME}}\right)^2 + \left(\frac{\sigma_U}{U}\right)^2 + \left(\frac{\sigma_L}{L}\right)^2}$$
$$\text{CI}_{95\%} = \left[ Q - 1.96 \sigma_Q, \; Q + 1.96 \sigma_Q \right]$$

---

## 🚀 التشغيل على أي جهاز والرفع المجاني على السحابة (Local & Free Cloud Hosting)

> **التوليد الذاتي الذكي (Zero-Config Self-Bootstrapping):** يعمل المشروع فوراً من أي جهاز جديد بمجرد عمل `git clone` أو على أي سيرفر سحابي دون الحاجة لنقل ملفات `.nc` الكبيرة؛ حيث يقوم النظام تلقائياً ببناء المشاهد الأربعة (بما فيها مشهد رحلة ناسا الحقيقية **Orbit 2222205 — Plume Complex 485**) في أقل من ثانيتين عند أول إقلاع.

### 1️⃣ التشغيل المحلي على أي لابتوب (Windows / macOS / Linux):
* **على ويندوز (ضغطة واحدة):** اضغط مرتين على `run_demo.bat`
* **على أي نظام تشغيل (Windows / Mac / Linux):**
```bash
python run_demo.py
```
يقوم المشغل تلقائياً بتثبيت أي حزم ناقصة، وتخطي شاشة البريد الإلكتروني التفاعلية لـ Streamlit، والتحقق من المشاهد والأوزان العصبية، ثم فتح لوحة التحكم على `http://localhost:8501`.

### 2️⃣ الرفع السحابي المجاني الدائم برابط عام (Streamlit Community Cloud — 100% Free):
1. افتح موقع [share.streamlit.io](https://share.streamlit.io) وسجل الدخول بحساب **GitHub**.
2. اضغط **Create app** واختر المستودع: `Mo-Shino/NASA-Methane-Plume-Detection-ISEF-2027` والفرع `main`.
3. حدد مسار الملف الرئيسي (`Main file path`): `app.py` ثم اضغط **Deploy**.
4. خلال دقيقتين تحصل على رابط سحابي عام دائم (`https://spectraplume.streamlit.app`) يفتح فوراً من أي موبايل أو تابلت أو جهاز محكم عبر رمز QR!

### 3️⃣ النشر عبر Docker أو Hugging Face Spaces:
المستودع مزود بملف `Dockerfile` خفيف يعتمد على نسخة المعالج القياسية لـ PyTorch لتسريع البناء السحابي:
```bash
docker build -t spectraplume .
docker run -p 8501:7860 -e PORT=7860 spectraplume
```

### 4️⃣ تشغيل حزمة الاختبارات العلمية الآلية (8 اختبارات):
```bash
python -m unittest tests/test_physics_and_pipeline.py -v
```

---

## 👥 فريق العمل (Team Identity)
* **المشروع:** SpectraPlume Framework
* **الفئة:** Earth & Environmental Sciences (EAEV) — Atmospheric Science (AIR)
* **المسابقة:** Regeneron ISEF 2027
* **المدينة:** الإسكندرية، مصر
* *تنويه الامتثال لقواعد ISEF Rule 2:* لوحة العرض والواجهة البرمجية تلتزم بالسرية الصارمة ولا تتضمن أسماء الطلاب أو المدارس.

---

## 📄 الرخصة (License)
هذا المشروع مفتوح المصدر ومرخص تحت رخصة **MIT License**.
