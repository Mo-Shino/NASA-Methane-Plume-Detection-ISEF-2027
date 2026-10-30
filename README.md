# SpectraPlume: Autonomous Spaceborne Methane Radar & Flux Quantification
### Regeneron ISEF 2027 Research Project | Alexandria, Egypt
**Autonomous Super-Emitter Methane Plume Detection & Mass Flux Quantification from NASA EMIT Hyperspectral Satellite Data via Spatial-Spectral Computer Vision & Radiative Transfer Inversion**

[![ISEF 2027](https://img.shields.io/badge/Competition-Regeneron%20ISEF%202027-blue.svg)](https://www.societyforscience.org/isef/)
[![Category](https://img.shields.io/badge/Category-Earth%20%26%20Environmental%20Sciences%20(EAEV)-emerald.svg)](#)
[![Sub-Category](https://img.shields.io/badge/Sub--Category-Atmospheric%20Science%20(AIR)-teal.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![NASA EMIT](https://img.shields.io/badge/Data-NASA%20EMIT%20L2A%2FL2B-orange.svg)](https://earth.jpl.nasa.gov/emit/)

---

## 📌 ملخص المشروع (Project Abstract)

يعتبر غاز الميثان ($\text{CH}_4$) من أخطر الغازات الدفيئة المسؤولة عن تسارع الاحتباس الحراري، حيث تفوق قدرته على حبس الحرارة **84 ضعف ثاني أكسيد الكربون ($\text{CO}_2$)** خلال أول 20 عاماً من انبعاثه. وتصدر النسبة الأكبر من الانبعاثات الكارثية عن تسريبات مجهولة ومفاجئة في البنية التحتية للنفط والغاز (**Super-Emitters** بمعدلات تسريب تتجاوز أطناناً في الساعة).

يقدم مشروع **SpectraPlume** منظومة برمجية وفيزيائية متكاملة ذاتية التشغيل بالرؤية الحاسوبية المكانية-الطيفية (Autonomous Spatial-Spectral Vision Framework) تعمل على:
1. **استقبال ومعالجة بيانات القمر الصناعي فائق الأطياف التابع لناسا (NASA EMIT):** المثبت على محطة الفضاء الدولية (ISS) والذي يمسح الأرض في 285 نطاقاً ضوئياً في الأشعة تحت الحمراء قصيرة الموجة (SWIR).
2. **عزل سحب الميثان الشفافة ذاتياً:** دون الحاجة لأي تدخل بشري عبر خوارزمية المرشح المطابق الموحد (Unit Matched Filter).
3. **القضاء التام على الإنذارات الكاذبة:** التغلب على معضلة تداخل بصمة صخور الكربونات والكالسيت ($2.3\,\mu\text{m}$) بنسبة خفض تجاوزت **94.7%**.
4. **التقدير اللحظي لمعدل التسريب الكتلي ($Q \pm \sigma_Q$):** حساب معدل التدفق بالطن/ساعة بنموذج التراكم الكتلي المتكامل (IME) مع دمج سرعات رياح ERA5 ونمذجة هامش الخطأ ومجال الثقة 95%.
5. **إسقاط جغرافي دقيق على صور الأقمار الصناعية (GIS Satellite Imagery):** لتحديد موقع الفالف أو الخزان المسرب على خريطة Esri الفضائية وإصدار تقارير طوارئ رقمية معتمدة.

---

## 🏛️ الهيكل التنظيمي للمستودع (Repository Structure)

```text
NASA-Methane-Plume-Detection-ISEF-2027/
│
├── 🚀 run_demo.bat                   <-- [ضغطة واحدة] تشغيل النظام وفحص الاعتماديات وفتح لوحة التحكم
├── 🌐 app.py                          <-- لوحة التحكم المباشرة للمهمة (Streamlit Mission Control Center)
├── ⚙️ pipeline_runner.py              <-- خط المعالجة المتكامل (End-to-End Processing Engine)
├── 🧠 train_model.py                  <-- تدريب ومعايرة أوزان شبكة الانتباه المكاني-الطيفي
├── 🔑 setup_earthdata.py              <-- أداة ربط وتوثيق حساب NASA Earthdata والـ Token
├── 📦 requirements.txt               <-- حزم بايثون البرمجية المطلوبة
├── 📖 README.md                       <-- وثيقة الترحيب والتشغيل الرئيسية
│
├── 📂 src/                            <-- المحركات الفيزيائية والخوارزميات الأساسية
│   ├── benchmark_generator.py         <-- مولد مكعبات الأطياف الفيزيائية بنموذج الانتقال الإشعاعي
│   ├── data_loader.py                 <-- معالج بيانات ناسا (NetCDF4, HDF5, Earthaccess)
│   ├── flux_calculator.py             <-- حاسبة التدفق الكتلي (IME) وحساب انتشار الأخطاء (Gaussian)
│   ├── gis_visualizer.py              <-- محرك الخرائط الفضائية التفاعلية (Esri World Imagery)
│   ├── matched_filter.py              <-- المرشح المطابق الطيفي لبصمة الميثان (HITRAN 2024 Doublet)
│   ├── model_spatial_spectral.py      <-- البنية العصبية للرؤية المكانية-الطيفية (Dual-Branch Gated CNN)
│   └── real_granule_fetcher.py        <-- أداة الاستعلام المباشر وتنزيل الـ Granules من سيرفرات ناسا
│
├── 📂 tests/                          <-- الاختبارات العلمية والفيزيائية الآلية
│   └── test_physics_and_pipeline.py   <-- 5 اختبارات وحدة صارمة (HITRAN, IME, NetCDF, Error Bounds)
│
├── 📂 data/                           <-- مجموعات البيانات ومشاهد الأقمار الصناعية
│   ├── benchmark_scenes/              <-- مشاهد اختبار فيزيائية قياسية بـ Ground Truth معلوم
│   └── real_emit/                     <-- مشاهد حقيقية تم سحبها مباشرة من خوادم NASA LP DAAC
│
├── 📂 weights/                        <-- الأوزان العصبية المعايرة للنموذج
│   └── spatial_spectral_emit.pt       <-- أوزان شبكة الـ Dual-Branch Gated CNN
│
├── 📂 docs/                           <-- الوثائق البحثية والمواصفات الفيزيائية
│   ├── README.md                      <-- فهرس الوثائق البحثية
│   ├── 01_RESEARCH_SPECIFICATION.md   <-- المواصفات الفيزيائية والنظرية لقمر EMIT ومعادلات HITRAN
│   ├── 02_PROTOTYPE_EXECUTION_MASTERPLAN.md <-- المخطط الهندسي التنفيذي للمنظومة
│   ├── 03_MASTER_RESEARCH_AND_IMPLEMENTATION.md <-- الاشتقاقات الرياضية للـ Matched Filter والـ IME
│   ├── 04_NASA_EARTHDATA_LOGIN_GUIDE.pdf <-- دليل توثيق الحساب على خوادم ناسا
│   ├── 05_IMPLEMENTATION_SUMMARY.pdf  <-- الملخص التنفيذي للمشروع
│   └── archive/                       <-- أرشيف الدراسات المرجعية ومصفوفات المقارنة السابقة
│
└── 📂 display_board/                  <-- لوحة العرض الرسمية لمسابقة ISEF والتصميمات
    ├── README.md                      <-- معايير العرض وأبعاد اللوحة
    ├── Display_Board_Official.pdf     <-- لوحة العرض الرسمية جاهزة للطباعة عالية الدقة
    ├── Display_Board_Template_ISEF.pptx <-- قالب PowerPoint التفاعلي المفتوح للتعديل
    ├── display_board_100x70.html      <-- تصميم اللوحة التفاعلي بـ HTML/CSS بدقة الفكتور
    ├── html_board_rendered_full.png   <-- معاينة بصرية كاملة للوحة العرض
    ├── DISPLAY_BOARD_STRATEGY.md      <-- الدليل التكتيكي للرد على أسئلة المحكمين وتحقيق المركز الأول
    └── clean_logos/                   <-- شعارات وكالة ناسا ومحطة الفضاء بجودة فائقة وQR المستودع
```

---

## 🔬 الأسس العلمية والرياضية (Mathematical Formulation)

### 1. المرشح المطابق الطيفي الموحد (Unit-Normalized Matched Filter)
$$\alpha(x) = \frac{(x - \mu)^T \Sigma_{\text{reg}}^{-1} t}{t^T \Sigma_{\text{reg}}^{-1} t}$$
* $x \in \mathbb{R}^B$: طيف الانعكاسية المقاس للبكسل عبر 40 نطاقاً طيفياً في نافذة $2150 - 2450\,\text{nm}$.
* $\mu \in \mathbb{R}^B$: متوسط انعكاسية الخلفية المحلية للمشهد.
* $\Sigma_{\text{reg}} = \Sigma + \lambda I$: مصفوفة التغاير المنظمة مع عامل الاستقرار التكيفي $\lambda$.
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

## 🚀 كيفية التشغيل والعرض المباشر (Quickstart & Demo)

### الطريقة الأسرع (ضغطة واحدة على ويندوز):
اضغط مرتين على ملف:
```text
run_demo.bat
```
سيقوم السكربت بفحص المكتبات، التأكد من ملفات الأوزان ومشاهد الأقمار الصناعية، وتشغيل لوحة التحكم التفاعلية على الرابط:
`http://localhost:8501`

### التشغيل عبر سطر الأوامر (Command Line):
```powershell
# 1. تفعيل بيئة العمل وتثبيت الحزم (إن لم تكن مثبتة)
pip install -r requirements.txt

# 2. تشغيل لوحة التحكم
streamlit run app.py
```

### تشغيل الاختبارات العلمية الآلية:
```powershell
python -m unittest tests/test_physics_and_pipeline.py
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
