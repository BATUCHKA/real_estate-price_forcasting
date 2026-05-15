# Quarto тайлан

## Render хийх

### 1. Quarto суулгах

```bash
brew install --cask quarto
```

эсвэл [quarto.org/docs/get-started](https://quarto.org/docs/get-started/)-аас татаж суулгах.

### 2. PDF болгох

Эх төслийн язгуураас:

```bash
cd report
quarto render report.qmd --to pdf
```

Хэрэв Python-ийн venv ашиглаж байвал:

```bash
QUARTO_PYTHON=../.venv/bin/python quarto render report.qmd --to pdf
```

Үр дүн: `report/report.pdf`

### 3. HTML preview-тэй render

```bash
quarto preview report.qmd
```

## LaTeX суулгах

Quarto-д PDF render хийхэд **xelatex** хэрэгтэй (mongol үсэг дэмжихийн тулд):

```bash
brew install --cask mactex-no-gui
# эсвэл хөнгөн вариант:
quarto install tinytex
```

## Файлуудын тайлбар

- `report.qmd` — Quarto эх файл (текст + код)
- `references.bib` — BibTeX цуглуулга (APA)
- `apa.csl` — APA citation style (citation-style-language/styles-аас татсан)
- `report.pdf` — Эцсийн тайлан (render хийсний дараа үүснэ)

## Анхаар

- `data/listings.csv` ба `data/listings_clean.csv` файлууд **эх төслийн `data/`** фолдер дотор байх ёстой
- Python хамаарлууд суусан байх ёстой: `pip install -r ../requirements.txt`
