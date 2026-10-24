# NASA EMIT Methane Plume Detection & Flux Quantification Framework
### Regeneron ISEF 2027 Research Project | Alexandria, Egypt
**Autonomous Super-Emitter Methane Plume Detection & Flux Rate Quantification from NASA EMIT Hyperspectral Satellite Data via Spatial-Spectral Computer Vision**

[![ISEF 2027](https://img.shields.io/badge/Competition-Regeneron%20ISEF%202027-blue.svg)](https://www.societyforscience.org/isef/)
[![Category](https://img.shields.io/badge/Category-Earth%20%26%20Environmental%20Sciences%20(EAEV)-emerald.svg)](#)
[![Secondary Category](https://img.shields.io/badge/Secondary-Systems%20Software%20(SOFT)-purple.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2%2B-ee4c2c.svg)](https://pytorch.org/)

---

## 📌 نبذة سريعة وملخص المشروع (Project Overview)

يعتبر غاز الميثان ($\text{CH}_4$) ثاني أهم الغازات الدفيئة المسؤولة عن الاحتباس الحراري السريع بعد ثاني أكسيد الكربون، إلا أن قدرته على حبس الحرارة تعادل **84 ضعف قدرة $\text{CO}_2$ على مدار 20 عاماً**. تكمن المشكلة الكبرى في أن معظم انبعاثات الميثان الكارثية تصدر عن تسريبات مفاجئة غير مرئية في خطوط أنابيب النفط والغاز، ومحطات الضغط، ومكبات النفايات العملاقة (تسمى علمياً **Super-Emitters** بمعدلات تسريب تتجاوز أطناناً في الساعة).

يهدف هذا المشروع لبناء **منظومة برمجية متكاملة ذاتية التشغيل بالذكاء الاصطناعي والرؤية الحاسوبية (Autonomous Spatial-Spectral Computer Vision Pipeline)** تعمل على:
1. معالجة وتصفية بيانات القمر الصناعي فائق الأطياف التابع لوكالة ناسا الأمريكية **NASA EMIT** (المثبت على محطة الفضاء الدولية ويصور الأرض في 285 نطاقاً ضوئياً في الأشعة تحت الحمراء قصيرة الموجة SWIR).
2. كشف وعزل سحب الميثان الشفافة غير المرئية بدقة المتر الواحد دون الحاجة لأي تدخل بشري.
3. التغلب على معضلة "الإنذارات الكاذبة" الناتجة عن تداخل أطياف المعادن السطحية وصخور الكربونات مع طيف الميثان عند الطول الموجي $2.3\,\mu m$.
4. الحساب الكتلي الآلي اللحظي لمعدل التسريب (Emission Flux Rate $Q$) بالكيلوجرام والطن في الساعة باستخدام نموذج التراكم الكتلي المتكامل (IME) ودمج سرعات الرياح من نماذج الطقس العالمية (ERA5).
5. إصدار تنبيهات خرائطية فورية لشركات الطاقة والجهات البيئية لوقف التسريب فوراً وتوفير ملايين الدولارات من الغاز المفقود.

---

## 👥 فريق العمل وتوزيع الأدوار (Team Profile & Roles)

* **فارس (Fares - 18 سنة): مهندس النظم وهندسة البرمجيات (Systems & Data Architect)**
  * التخصص: C# / .NET Core, Backend Web APIs, Concurrency, Algorithms, System Design, Data Pipelines.
  * دوره في المشروع: بناء خط أنابيب سحب ومعالجة بيانات ناسا الضخمة (`data_loader.py`)، أتمتة تدريب نماذج الرؤية الحاسوبية في PyTorch، وتطوير لوحة التحكم والخرائط التفاعلية وإصدار التقارير.
* **الشناوي (Shnawy - 17 سنة): النمذجة الرياضية والفيزيائية (Physical & Mathematical Modeler)**
  * التخصص: الفيزياء، الجبر الخطي، معالجة الإشارات الرقمية، الديناميكا غير الخطية، والإحصاء.
  * دوره في المشروع: النمذجة الرياضية لطيف امتصاص الميثان (HITRAN Database)، اشتقاق خوارزمية المرشح المطابق (Matched Filter Derivation)، وتطبيق معادلات التدفق الكتلي وديناميكا انتشار السحب (IME Plume Flux Equations).

---

## 🏛️ الهيكل المعماري للمستودع (Repository Structure)

```
NASA-Methane-Plume-Detection-ISEF-2027/
│
├── README.md                              <- وثيقة الترحيب والتشغيل الرئيسية (أنت هنا)
├── NASA_METHANE_RESEARCH_SPECIFICATION.md <- المرجع البحثي والنظري والفيزيائي الشامل للمشروع
├── ISEF_ROUND2_MASTER_DOSSIER.md          <- الملف التاريخي الماستر لدراسة ISEF وقواعد التحكيم
├── ISEF_SELECTED_IDEAS.md                 <- القائمة المختصرة للمشاريع الستة السابقة
├── ISEF_FILTERED_CANDIDATES.html          <- لوحة التحكم التفاعلية الفخمة للأفكار (Light UI)
├── requirements.txt                       <- حزم بايثون المطلوبة للتشغيل
├── .gitignore                             <- استبعاد الملفات المؤقتة والبيانات الضخمة
│
├── src/                                   <- كود المصدر البرمجي الأساسي (Source Code)
│   ├── __init__.py
│   ├── data_loader.py                     <- سحب وتحميل بيانات NASA EMIT NetCDF4 (.nc)
│   ├── matched_filter.py                  <- خط الأساس: المرشح المطابق الطيفي الكلاسيكي (MF)
│   ├── model_spatial_spectral.py          <- الابتكار: شبكة الانتباه المكاني-الطيفي (Dual-Branch U-Net)
│   └── flux_calculator.py                 <- حساب التدفق الكتلي بالطن/ساعة بنموذج IME
│
├── docs/                                  <- أوراق بحثية ومراجع ومخططات هندسية
│   └── (يتم وضع صور السحب والمخططات التوضيحية هنا)
│
└── data/                                  <- مجلد البيانات (مستبعد من git لمنع تضخم الريبو)
    ├── raw/                               <- بيانات EMIT L2A Reflectance الخام
    └── cache/                             <- ملفات التخزين المؤقت
```

---

## 🔬 الأسس العلمية والرياضية (Mathematical Formulation)

### 1. المرشح المطابق الطيفي (Linearized Spectral Matched Filter)
$$\alpha(x) = \frac{(x - \mu)^T \Sigma_{\text{reg}}^{-1} t}{t^T \Sigma_{\text{reg}}^{-1} t}$$
* $x \in \mathbb{R}^B$: طيف الانعكاسية المقاس للبكسل عبر النطاقات الطيفية.
* $\mu \in \mathbb{R}^B$: متوسط انعكاسية السطح للخلفية المحلية المحيطة.
* $\Sigma_{\text{reg}} = \Sigma + \lambda I$: مصفوفة التغاير المنظمة لتفادي الشذوذ العددي.
* $t \in \mathbb{R}^B$: بصمة الامتصاص الكيميائي المرجعية للميثان عند $2.3\,\mu m$ (مستخلصة من HITRAN).
* $\alpha(x)$: كثافة عمود الميثان الزائد بوحدة $\text{ppm}\cdot\text{m}$.

### 2. نموذج التراكم الكتلي المتكامل لحساب التسريب (Integrated Mass Enhancement - IME)
$$\text{IME} = \sum_{i \in \text{Plume}} \Delta \Omega_i \cdot A_{\text{pixel}} \cdot k_{\text{CH}_4} \quad [\text{kg}]$$
$$Q = \frac{\text{IME} \cdot U_{\text{eff}}}{L} \times 3600 \quad [\text{kg/hr}]$$
* $\Delta \Omega_i$: كثافة عمود البكسل الزائدة ($\text{ppm}\cdot\text{m}$).
* $A_{\text{pixel}}$: مساحة البكسل الأرضي لقمر ناسا ($60\text{ m} \times 60\text{ m} = 3600\text{ m}^2$).
* $k_{\text{CH}_4} = 7.16 \times 10^{-7}\text{ kg/(m}^2 \cdot \text{ppm}\cdot\text{m)}$: ثابت التحويل الكتلي لجزيئات الميثان.
* $U_{\text{eff}}$: سرعة الرياح الفعالة على ارتفاع 10 أمتار من نموذج ERA5 الأوروبي.
* $L$: طول السحابة الفعلي على طول محور هبوب الرياح.

---

## 🚀 دليل البدء والتشغيل (Quickstart Guide)

### 1. استنساخ المستودع (Clone)
```bash
git clone https://github.com/Mo-Shino/NASA-Methane-Plume-Detection-ISEF-2027.git
cd NASA-Methane-Plume-Detection-ISEF-2027
```

### 2. إنشاء بيئة عمل بايثون وتثبيت المكتبات
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. إعداد حساب NASA Earthdata المجاني
* قم بالتسجيل للحصول على حساب مجاني من الرابط: [https://urs.earthdata.nasa.gov/](https://urs.earthdata.nasa.gov/)
* استخدم مكتبة `earthaccess` لتسجيل الدخول:
```python
import earthaccess
auth = earthaccess.login(strategy="interactive")
```

---

## 🤖 تعليمات خاصة لنموذج الذكاء الاصطناعي على اللابتوب الثاني
### (Instructions for the Next AI Agent)

> **عزيزي نموذج الذكاء الاصطناعي (Claude / Gemini / GPT):**  
> مرحباً بك في مستودع مشروع Regeneron ISEF 2027 لفريق فارس والشناوي. هذا المشروع ليس تمريناً مدرسياً عادياً، بل مشروع مصمم للمنافسة على **المركز الأول عالمياً (Grand Award / 1st Place)** في فئة علوم الأرض والبيئة (EAEV) أو برمجيات النظم (SOFT).
>
> **عند استئناف العمل مع الفريق على اللابتوب الجديد، اتبع البروتوكول التالي:**
> 1. اقرأ هذا الملف `README.md` وملف `NASA_METHANE_RESEARCH_SPECIFICATION.md` لفهم الإطار العلمي الدقيق ومعادلات الـ Matched Filter والـ IME.
> 2. فارس مطور Backend و C# محترف؛ والشناوي متميز في الرياضيات والفيزياء. ساعدهما في كتابة كود بايثون متقدم وشديد النظافة، مع شرح الخطوات البرمجية لفارس والرياضية للشناوي.
> 3. **الخطوة العملية الفورية التالية:**
>    * تشغيل اختبار تجريبي لـ `src/data_loader.py` و `src/matched_filter.py` على عينة مصغرة (Synthetic or Real EMIT Tile).
>    * تنزيل عينة إطار حقيقي معروف باحتوائه على تسريب ميثان ضخم (مثل حوض بيرميان في تكساس أو حقول تركمانستان من كتالوج Carbon Mapper).
>    * توليد خريطة الـ Matched Filter ومقارنتها بنتائج JPL الرسمية كـ Baseline.
>    * تدريب شبكة `src/model_spatial_spectral.py` لإلغاء الإنذارات الكاذبة الناتجة عن صخور الكربونات وأسطح المباني.
> 4. لا تقترح أبداً أفكاراً سطحية أو واجهات مستخدم تجارية مبسطة دون عمق علمي؛ المحكمون في ISEF يبحثون عن الأثر العلمي القابل للقياس، هوامش الخطأ، والتحليل الإحصائي المقارن.

---

## 📄 الرخصة (License)
هذا المشروع مرخص تحت رخصة **MIT License** المفتوحة للمساهمة في أبحاث المناخ العالمية.
