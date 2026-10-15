"""
Генератор тестовых данных для A/B-теста.
Создаёт три сценария:
  1) два независимых источника (google_ads.csv, yandex_direct.csv),
  2) сводная сырая таблица (raw_traffic.csv),
  3) готовая таблица под ab_test.py (experiment_users.csv).
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

np.random.seed(42)
Path("data").mkdir(exist_ok=True)

# --- параметры "реального" эксперимента ---
N_GOOGLE = 2000
N_YANDEX = 2000

P_GOOGLE = 0.050   # контроль (A)
P_YANDEX = 0.065   # тест (B), на +1.5 п.п. выше

DATE_START = datetime(2026, 9, 1)
DATE_END = datetime(2026, 9, 14)


def make_source(n, p, source, start_id):
    user_ids = np.arange(start_id, start_id + n)
    converted = np.random.binomial(1, p, size=n)

    days = np.random.randint(0, (DATE_END - DATE_START).days + 1, size=n)
    dates = [DATE_START + timedelta(days=int(d)) for d in days]

    return pd.DataFrame({
        "user_id": user_ids,
        "source": source,
        "converted_observed": converted,
        "date": dates,
    })


# --- 1. Два независимых источника ---
google = make_source(N_GOOGLE, P_GOOGLE, "google_ads", start_id=100_000)
yandex = make_source(N_YANDEX, P_YANDEX, "yandex_direct", start_id=200_000)

google.to_csv("data/google_ads.csv", index=False)
yandex.to_csv("data/yandex_direct.csv", index=False)

# --- 2. Сводная сырая таблица (как прилетает из рекламных систем) ---
raw = pd.concat([google, yandex], ignore_index=True)
raw = raw.sample(frac=1, random_state=1).reset_index(drop=True)
raw.to_csv("data/raw_traffic.csv", index=False)

# --- 3. Готовая таблица под ab_test.py ---
SOURCE_TO_GROUP = {
    "google_ads": "A",
    "yandex_direct": "B",
}

experiment = pd.concat([google, yandex], ignore_index=True)
experiment["group"] = experiment["source"].map(SOURCE_TO_GROUP)
experiment = experiment[["user_id", "group", "converted_observed"]]
experiment = experiment.sample(frac=1, random_state=1).reset_index(drop=True)
experiment.to_csv("data/experiment_users.csv", index=False)

# --- отчёт ---
print("Созданы файлы:")
print(f"  data/google_ads.csv        — источник 1, n={len(google)}")
print(f"  data/yandex_direct.csv     — источник 2, n={len(yandex)}")
print(f"  data/raw_traffic.csv       — сводная сырая таблица, n={len(raw)}")
print(f"  data/experiment_users.csv  — готовая под ab_test.py, n={len(experiment)}")

print("\nСводка по группам в experiment_users.csv:")
print(
    experiment
    .groupby("group")["converted_observed"]
    .agg(n="count", success="sum", conversion="mean")
    .assign(conversion=lambda d: d["conversion"].round(4))
)