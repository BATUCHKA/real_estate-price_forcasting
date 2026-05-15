"""
Үл хөдлөх хөрөнгийн үнэ таамаглах скрипт.

Random Forest загвараар үнийг таамаглана. Эхний удаа ажиллуулахад загварыг
сургаж `models/rf_model.joblib`-д хадгална. Дараагийн удаад хадгалсан загварыг
ачаалж шууд таамагладаг тул хурдан ажиллана.

Хэрэглээ:
    # Жишээ таамаглал
    python predict.py --examples

    # Тодорхой айл
    python predict.py --area 80 --rooms 3 --district Хан-Уул --age 5

    # Бүх параметр
    python predict.py \\
        --area 95 --rooms 3 --floor 7 --total-floors 12 \\
        --age 3 --district Сүхбаатар \\
        --balcony --garage --elevator --finished
"""

import argparse
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error

DATA_PATH = Path("data/listings_clean.csv")
MODEL_PATH = Path("models/rf_model.joblib")
RANDOM_STATE = 42

NUMERIC = ["area_m2", "rooms", "floor", "total_floors", "floor_ratio",
           "building_age", "has_balcony", "balcony_count", "has_garage",
           "has_elevator", "is_finished"]
CATEGORICAL = ["district_grouped", "window_type", "door_type", "floor_material"]


def train_and_save():
    """Загварыг сургаад файлд хадгална."""
    print("Загвар сургаж байна...")
    df = pd.read_csv(DATA_PATH)
    X = df[NUMERIC + CATEGORICAL]
    y = df["log_price"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    pre = ColumnTransformer([
        ("num", Pipeline([("i", SimpleImputer(strategy="median")),
                          ("s", StandardScaler())]), NUMERIC),
        ("cat", Pipeline([("i", SimpleImputer(strategy="constant", fill_value="unknown")),
                          ("o", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), CATEGORICAL),
    ])

    pipe = Pipeline([
        ("prep", pre),
        ("model", RandomForestRegressor(
            n_estimators=400, max_depth=None, min_samples_leaf=1,
            n_jobs=-1, random_state=RANDOM_STATE,
        )),
    ])
    pipe.fit(X_train, y_train)

    # Test үнэлгээ
    y_pred = pipe.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae_mnt = mean_absolute_error(np.exp(y_test), np.exp(y_pred)) / 1e6

    print(f"Сургалт дууссан → R² = {r2:.3f}, MAE = {mae_mnt:.1f} сая ₮")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, MODEL_PATH)
    print(f"Хадгаллаа → {MODEL_PATH}")
    return pipe


def load_model():
    if not MODEL_PATH.exists():
        return train_and_save()
    return joblib.load(MODEL_PATH)


def make_row(area, rooms, floor, total_floors, age, district,
             balcony=True, balcony_count=1, garage=False, elevator=True,
             finished=True, window_type="Вакум", door_type="Төмөр",
             floor_material="Паркет") -> pd.DataFrame:
    """Нэг айлыг загварт өгөх DataFrame болгож хувиргана."""
    return pd.DataFrame([{
        "area_m2": area,
        "rooms": rooms,
        "floor": floor,
        "total_floors": total_floors,
        "floor_ratio": floor / total_floors if total_floors else 0.5,
        "building_age": age,
        "has_balcony": int(balcony),
        "balcony_count": balcony_count,
        "has_garage": int(garage),
        "has_elevator": int(elevator),
        "is_finished": int(finished),
        "district_grouped": district,
        "window_type": window_type,
        "door_type": door_type,
        "floor_material": floor_material,
    }])


def predict(model, row: pd.DataFrame) -> float:
    """log_price-ийг exp-ээр буцааж бодит ₮ үнэ гаргана."""
    log_price = model.predict(row)[0]
    return float(np.exp(log_price))


def print_prediction(row: pd.DataFrame, price_mnt: float):
    r = row.iloc[0]
    print()
    print(f"  Талбай:           {r['area_m2']:.0f} м²")
    print(f"  Өрөө:             {int(r['rooms'])}")
    print(f"  Давхар:           {int(r['floor'])}/{int(r['total_floors'])}")
    print(f"  Барилгын нас:     {int(r['building_age'])} жил")
    print(f"  Дүүрэг:           {r['district_grouped']}")
    print(f"  Тагт/Гараж/Цахи:  {'✓' if r['has_balcony'] else '✗'}/{'✓' if r['has_garage'] else '✗'}/{'✓' if r['has_elevator'] else '✗'}")
    print(f"  → Таамагласан үнэ: {price_mnt/1e6:.1f} сая ₮  ({price_mnt/r['area_m2']/1e6:.2f} сая ₮/м²)")


def run_examples(model):
    """Жишээ айлуудын үнийг таамаглаж харуулна."""
    examples = [
        ("Жижиг өрөөтэй айл (Баянгол)",
         dict(area=45, rooms=2, floor=4, total_floors=9, age=15, district="Баянгол")),
        ("Дунд айл (Хан-Уул, шинэ хотхон)",
         dict(area=80, rooms=3, floor=7, total_floors=16, age=2, district="Хан-Уул")),
        ("Том айл (Сүхбаатар, гараж + тагт)",
         dict(area=130, rooms=4, floor=8, total_floors=12, age=5, district="Сүхбаатар",
              garage=True, balcony_count=2)),
        ("Хуучин барилга (Чингэлтэй)",
         dict(area=60, rooms=2, floor=3, total_floors=5, age=35, district="Чингэлтэй",
              elevator=False)),
        ("Шинэ том айл (Сүхбаатар, дээд зэргийн)",
         dict(area=180, rooms=5, floor=14, total_floors=20, age=0, district="Сүхбаатар",
              garage=True, balcony_count=2)),
    ]
    for title, params in examples:
        row = make_row(**params)
        price = predict(model, row)
        print(f"\n━━━ {title} ━━━")
        print_prediction(row, price)


def main():
    p = argparse.ArgumentParser(description="Үл хөдлөх хөрөнгийн үнэ таамаглах")
    p.add_argument("--examples", action="store_true", help="Жишээ таамаглал харуулах")
    p.add_argument("--retrain", action="store_true", help="Загварыг дахин сургах")
    p.add_argument("--area", type=float, help="Талбай (м²)")
    p.add_argument("--rooms", type=int, default=2, help="Өрөөний тоо")
    p.add_argument("--floor", type=int, default=5, help="Хэдэн давхарт")
    p.add_argument("--total-floors", type=int, default=10, help="Нийт давхар")
    p.add_argument("--age", type=int, default=5, help="Барилгын нас (жил)")
    p.add_argument("--district", default="Хан-Уул",
                   choices=["Хан-Уул", "Баянзүрх", "Сүхбаатар", "Баянгол",
                            "Сонгинохайрхан", "Чингэлтэй", "Бусад"],
                   help="Дүүрэг")
    p.add_argument("--balcony", action="store_true", help="Тагттай")
    p.add_argument("--garage", action="store_true", help="Гараж бий")
    p.add_argument("--elevator", action="store_true", help="Цахилгаан шаттай")
    p.add_argument("--finished", action="store_true", help="Ашиглалтад орсон")

    args = p.parse_args()

    if args.retrain and MODEL_PATH.exists():
        MODEL_PATH.unlink()

    model = load_model()

    if args.examples:
        run_examples(model)
        return

    if args.area is None:
        print("--examples ашиглах эсвэл --area параметр өгнө үү. --help харна уу.")
        sys.exit(1)

    row = make_row(
        area=args.area, rooms=args.rooms, floor=args.floor,
        total_floors=args.total_floors, age=args.age, district=args.district,
        balcony=args.balcony, garage=args.garage,
        elevator=args.elevator, finished=args.finished,
    )
    price = predict(model, row)
    print_prediction(row, price)


if __name__ == "__main__":
    main()
