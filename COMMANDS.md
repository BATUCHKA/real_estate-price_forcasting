# Төслийн бүх командын товч жагсаалт

## 1. Анхны суурилуулалт (нэг л удаа)

```bash
# Project руу шилжих
cd /Users/bataaboldbaatar/num/2025-havar/magadlal

# Python virtual environment үүсгэх
python3 -m venv .venv

# Хамаарал суулгах
.venv/bin/pip install -r requirements.txt

# Quarto суулгах (тайлан PDF болгоход)
brew install --cask quarto
quarto install tinytex
```

## 2. Өгөгдөл цуглуулах (Scraping)

```bash
# Туршилт — 1 хуудас (~60 зар, ~2 мин)
.venv/bin/python scrape_unegui.py --pages 1 --out data/test.csv

# Бүрэн — 50 хуудас (~3000 зар, ~2 цаг)
.venv/bin/python scrape_unegui.py --pages 50 --out data/listings.csv

# Тодорхой хуудаснаас эхлэх
.venv/bin/python scrape_unegui.py --pages 20 --start 51 --out data/listings.csv

# Шөнө background-аар (терминал хааж болно)
nohup .venv/bin/python scrape_unegui.py --pages 50 --out data/listings.csv > scrape.log 2>&1 &
tail -f scrape.log   # явц хянах
```

## 3. Notebook-уудыг ажиллуулах

```bash
# Интерактив горимоор
.venv/bin/jupyter notebook notebooks/02_clean.ipynb
.venv/bin/jupyter notebook notebooks/03_eda.ipynb
.venv/bin/jupyter notebook notebooks/04_models.ipynb

# Терминалаас шууд бүгдийг (inplace, үр дүн хадгална)
cd notebooks
../.venv/bin/jupyter nbconvert --to notebook --execute 02_clean.ipynb --inplace
../.venv/bin/jupyter nbconvert --to notebook --execute 03_eda.ipynb --inplace
../.venv/bin/jupyter nbconvert --to notebook --execute 04_models.ipynb --inplace
```

## 4. Үнэ таамаглах (`predict.py`)

```bash
# Тусламж
.venv/bin/python predict.py --help

# 5 жишээ айл
.venv/bin/python predict.py --examples

# Хамгийн энгийн
.venv/bin/python predict.py --area 80

# Дунд параметртэй
.venv/bin/python predict.py --area 80 --rooms 3 --district Сүхбаатар --age 3 --balcony --elevator

# 2 тагттай
.venv/bin/python predict.py --area 90 --rooms 3 --district Хан-Уул --balcony-count 2 --elevator

# Бүрэн параметртэй
.venv/bin/python predict.py \
    --area 150 --rooms 4 --floor 12 --total-floors 20 --age 1 \
    --district Сүхбаатар \
    --balcony-count 2 --garage --elevator --finished

# Загвар шинэчлэх (өгөгдөл шинэчилсний дараа)
.venv/bin/python predict.py --retrain --examples
```

### Бүх параметрийн жагсаалт

| Параметр | Үйлдэл / утга |
|---|---|
| `--help`, `-h` | Тусламж |
| `--examples` | 5 жишээ айлын таамаглал |
| `--retrain` | Загварыг шинэчлэн сургах |
| `--area` | Талбай (м²), заавал |
| `--rooms` | Өрөөний тоо (default: 2) |
| `--floor` | Хэдэн давхарт (default: 5) |
| `--total-floors` | Нийт давхар (default: 10) |
| `--age` | Барилгын нас, жил (default: 5) |
| `--district` | `Хан-Уул`, `Баянзүрх`, `Сүхбаатар`, `Баянгол`, `Сонгинохайрхан`, `Чингэлтэй`, `Бусад` |
| `--balcony` | Тагттай (1 тагт) |
| `--balcony-count N` | Тагтны тоо (0, 1, 2 ...) |
| `--garage` | Гараж бий |
| `--elevator` | Цахилгаан шаттай |
| `--finished` | Ашиглалтад орсон |

## 5. Quarto тайлан/үзүүлэн render хийх

```bash
# Тайлан PDF
cd report
QUARTO_PYTHON=../.venv/bin/python quarto render report.qmd --to pdf
open report.pdf

# Үзүүлэн HTML (танилцуулга)
cd presentation
QUARTO_PYTHON=../.venv/bin/python quarto render slides.qmd
open slides.html
# Зөвлөмж: HTML дотор F товч → full screen, S → speaker view

# Үзүүлэн PDF (хураалгах)
QUARTO_PYTHON=../.venv/bin/python quarto render slides.qmd --to pdf

# Live preview (засвар хийх үед)
quarto preview report.qmd
```

## 6. Git ажил

```bash
# Төлөв шалгах
git status
git log --oneline -5

# Өөрчлөлт commit & push
git add .
git commit -m "Богино тайлбар"
git push

# Дахин нэгтгэх
git pull
```

## 7. Хэрэгтэй туслах командууд

```bash
# Цэвэр өгөгдлийг шалгах
.venv/bin/python -c "import pandas as pd; df = pd.read_csv('data/listings_clean.csv'); print(df.shape); print(df.describe())"

# Загварыг устгаад дахин сургах
rm -rf models/
.venv/bin/python predict.py --examples

# Бүгдийг 0-ээс эхэлж дахин ажиллуулах
rm data/listings_clean.csv
.venv/bin/jupyter nbconvert --to notebook --execute notebooks/02_clean.ipynb --inplace
```

## 8. Хураалгахын өмнө шалгах

```bash
# Бүх файл бий эсэх
ls data/listings.csv data/listings_clean.csv \
   report/report.pdf presentation/slides.html \
   scrape_unegui.py predict.py \
   notebooks/02_clean.ipynb notebooks/03_eda.ipynb notebooks/04_models.ipynb

# PDF харах
open report/report.pdf
open presentation/slides.html
```

---

## Бүх дараалал (нэг хүн анхнаас нь хийх бол)

```bash
# 1. Setup
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 2. Өгөгдөл (нэг шөнө)
.venv/bin/python scrape_unegui.py --pages 50 --out data/listings.csv

# 3. Notebooks (~5 минут)
cd notebooks
../.venv/bin/jupyter nbconvert --to notebook --execute 02_clean.ipynb --inplace
../.venv/bin/jupyter nbconvert --to notebook --execute 03_eda.ipynb --inplace
../.venv/bin/jupyter nbconvert --to notebook --execute 04_models.ipynb --inplace
cd ..

# 4. Predict шалгах
.venv/bin/python predict.py --examples

# 5. Тайлан & үзүүлэн PDF
cd report && QUARTO_PYTHON=../.venv/bin/python quarto render report.qmd --to pdf && cd ..
cd presentation && QUARTO_PYTHON=../.venv/bin/python quarto render slides.qmd && cd ..

# 6. Git push
git add . && git commit -m "Бүх өөрчлөлт" && git push
```

---

## Эрсдэл, анхаарах зүйлс

- **Scraping үед терминал хааж болохгүй** — хэрэв 2 цаг ажиллуулна гэвэл `nohup` хэрэглээрэй
- **Notebook ажиллуулахдаа `cwd`** — `notebooks/` дотроос ажиллуулсан тохиолдолд relative path `../data/...` гэж байх ёстой
- **Quarto render үед** Python venv-ийг олох тулд `QUARTO_PYTHON` env variable хэрэглэнэ
- **Git commit мессеж**: богино, нэг мөртэй, Co-Authored-By залгахгүй

## GitHub repo

[BATUCHKA/real_estate-price_forcasting](https://github.com/BATUCHKA/real_estate-price_forcasting)
