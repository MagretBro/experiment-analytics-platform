from pathlib import Path
from datetime import datetime

import pandas as pd
from scipy.stats import norm
from src.data_diagnostics import diagnose_dataset
from src.data_quality import load_experiment_data, run_data_quality_checks
from src.save_results import save_ab_test_result
from src.save_data_quality import save_data_quality_results
from src.interpretation import generate_interpretation, save_interpretation


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"


def create_run_folder(base_path=RESULTS_DIR):
    run_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_path = Path(base_path) / run_id
    run_path.mkdir(parents=True, exist_ok=True)
    return run_id, run_path

# =========================
# 1. Создание папки запуска
# =========================

run_id, run_path = create_run_folder()

print(f"Run ID: {run_id}")
print(f"Результаты сохраняются в: {run_path}")

# =========================
# 2. Загрузка данных
# =========================

df = load_experiment_data(DATA_DIR / "experiment_users.csv")

# Этап 1. Исследование данных
diagnostics = diagnose_dataset(
    df,
    metric_column="converted_observed",
    group_column="group",
    id_column="user_id",
)

diagnostics_path = run_path / "diagnostics.csv"
diagnostics.to_csv(
    diagnostics_path,
    index=False,
    encoding="utf-8-sig",
)

print(f"Диагностика сохранена: {diagnostics_path}")
print("\n=== ДИАГНОСТИКА ДАННЫХ ===")
print(
    diagnostics[
        ["scope", "category", "check", "value", "status", "comment"]
    ].to_string(index=False)
)

# Этап 2. Проверка обязательных условий качества
quality_passed, quality_checks = run_data_quality_checks(df)

quality_path = save_data_quality_results(
    run_path,
    quality_checks
)

print(f"Результаты Data Quality сохранены: {quality_path}")

if not quality_passed:
    print("Анализ остановлен из-за ошибок качества данных.")
    exit()

# =========================
# 3. Группы A и B
# =========================

group_a = df[df["group"] == "A"]["converted_observed"]
group_b = df[df["group"] == "B"]["converted_observed"]


n_a = len(group_a)
n_b = len(group_b)

success_a = group_a.sum()
success_b = group_b.sum()


# =========================
# 4. Конверсия
# =========================

conversion_a = success_a / n_a
conversion_b = success_b / n_b


# =========================
# 5. Absolute uplift
# =========================

absolute_uplift = conversion_b - conversion_a


# =========================
# 5. Relative uplift
# =========================

relative_uplift = absolute_uplift / conversion_a


# =========================
# 6. Z-test
# =========================

pooled_conversion = (
    success_a + success_b
) / (
    n_a + n_b
)


se_test = (
    pooled_conversion
    * (1 - pooled_conversion)
    * (1 / n_a + 1 / n_b)
) ** 0.5


z_stat = absolute_uplift / se_test

p_value = 2 * (1 - norm.cdf(abs(z_stat)))


# =========================
# 7. 95% Confidence Interval
# =========================

se_ci = (
    conversion_a * (1 - conversion_a) / n_a
    +
    conversion_b * (1 - conversion_b) / n_b
) ** 0.5


z_critical = norm.ppf(0.975)


ci_lower = absolute_uplift - z_critical * se_ci
ci_upper = absolute_uplift + z_critical * se_ci


# =========================
# 8. Результат
# =========================

alpha = 0.05
statistically_significant = p_value < alpha


print("=== A/B TEST ===")

print(f"\nГруппа A: {success_a}/{n_a}")
print(f"Конверсия A: {conversion_a:.2%}")

print(f"\nГруппа B: {success_b}/{n_b}")
print(f"Конверсия B: {conversion_b:.2%}")

print("\n--- EFFECT ---")

print(
    f"Absolute uplift (B - A): "
    f"{absolute_uplift:.2%}"
)

print(
    f"Relative uplift: "
    f"{relative_uplift:.2%}"
)

print("\n--- STATISTICS ---")

print(f"Z-statistic: {z_stat:.3f}")
print(f"P-value: {p_value:.4f}")

print(
    f"95% CI for difference: "
    f"[{ci_lower:.2%}; {ci_upper:.2%}]"
)

print(f"\nAlpha: {alpha}")


if p_value < alpha:
    print(
        "\nРезультат статистически значим. "
        "Есть основания считать, что конверсия групп отличается."
    )
else:
    print(
        "\nСтатистически значимой разницы не обнаружено. "
        "Недостаточно оснований утверждать, что группы отличаются."
    )

# =========================
# 9. Сохранение результата
# =========================

result_path = save_ab_test_result(
    run_path=run_path,
    n_a=n_a,
    success_a=success_a,
    conversion_a=conversion_a,
    n_b=n_b,
    success_b=success_b,
    conversion_b=conversion_b,
    absolute_uplift=absolute_uplift,
    relative_uplift=relative_uplift,
    z_stat=z_stat,
    p_value=p_value,
    ci_lower=ci_lower,
    ci_upper=ci_upper,
    alpha=alpha,
    statistically_significant=statistically_significant
)

print(f"\nРезультат сохранён: {result_path}")
# =========================
# 11. Формирование интерпретации
# =========================

report = generate_interpretation(
    run_id=run_id,
    n_a=n_a,
    success_a=success_a,
    conversion_a=conversion_a,
    n_b=n_b,
    success_b=success_b,
    conversion_b=conversion_b,
    absolute_uplift=absolute_uplift,
    relative_uplift=relative_uplift,
    z_stat=z_stat,
    p_value=p_value,
    ci_lower=ci_lower,
    ci_upper=ci_upper,
    alpha=alpha
)

report_path = save_interpretation(
    run_path,
    report
)

print(f"Интерпретация сохранена: {report_path}")

# =========================
# 12. Человекочитаемая сводка
# =========================

human_path = run_path / "result_human.csv"

with open(human_path, "w", encoding="utf-8") as f:
    f.write("Показатель,Группа A,Группа B\n")
    f.write(f"Пользователей,{n_a},{n_b}\n")
    f.write(f"Конверсий,{success_a},{success_b}\n")
    f.write(f"Конверсия,{conversion_a:.2%},{conversion_b:.2%}\n")
    f.write("\n")
    f.write("Показатель,Значение\n")
    f.write(f"Абсолютный прирост (B − A),{absolute_uplift:+.2%}\n")
    f.write(f"Относительный прирост,{relative_uplift:+.2%}\n")
    f.write(f"Z-статистика,{z_stat:.3f}\n")
    f.write(f"p-value,{p_value:.4f}\n")
    f.write(f"95% CI,[{ci_lower:+.2%}; {ci_upper:+.2%}]\n")
    f.write(f"α,{alpha}\n")
    lines_verdict = "значимо" if statistically_significant else "НЕ значимо"
    f.write(f"Итог,{lines_verdict}\n")

print(f"Человекочитаемая сводка: {human_path}")