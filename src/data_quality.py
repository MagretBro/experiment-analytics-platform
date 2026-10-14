import pandas as pd
from scipy.stats import chisquare

REQUIRED_COLUMNS = [
    "user_id",
    "group",
    "converted_observed"
]

# =========================
# Expected group ratio
# =========================

EXPECTED_GROUP_RATIO = {
    "A": 0.5,
    "B": 0.5
}

SRM_ALPHA = 0.05


def load_experiment_data(file_path):
    return pd.read_csv(file_path)


def run_data_quality_checks(df):
    """
    Выполняет проверки качества данных.

    Возвращает:
        quality_passed: bool
        checks: list[dict]
    """

    checks = []

    if df.empty:
        checks.append({
            "check": "non_empty_dataset",
            "status": "FAIL",
            "description": "Датасет пустой"
        })
        print("Проверки качества данных остановлены: датасет пустой.")
        return False, checks    

    # =========================
    # 1. Required columns
    # =========================

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if not missing_columns:
        status = "PASS"
        description = "Все необходимые колонки присутствуют"
    else:
        status = "FAIL"
        description = (
            f"Отсутствуют колонки: {', '.join(missing_columns)}"
        )

    checks.append({
        "check": "required_columns",
        "status": status,
        "description": description
    })

    if missing_columns:
        print("Проверки качества данных остановлены: отсутствуют обязательные колонки.")
        return False, checks

    # =========================
    # 2. Missing values
    # =========================

    missing_count = df[REQUIRED_COLUMNS].isnull().sum().sum()

    if missing_count == 0:
        status = "PASS"
        description = "Пропуски отсутствуют"
    else:
        status = "FAIL"
        description = (
            f"Обнаружено пропусков: {missing_count}"
        )

    checks.append({
        "check": "missing_values",
        "status": status,
        "description": description
    })

    # =========================
    # 3. Unique user_id
    # =========================

    duplicate_count = df["user_id"].duplicated().sum()

    if duplicate_count == 0:
        status = "PASS"
        description = "user_id уникален"
    else:
        status = "FAIL"
        description = (
            f"Обнаружено дубликатов user_id: {duplicate_count}"
        )

    checks.append({
        "check": "unique_user_id",
        "status": status,
        "description": description
    })

    # =========================
    # 4. Valid groups
    # =========================

    valid_groups = {"A", "B"}
    actual_groups = set(df["group"].dropna().unique())

    invalid_groups = actual_groups - valid_groups

    if not invalid_groups:
        status = "PASS"
        description = "Используются только группы A и B"
    else:
        status = "FAIL"
        description = (
            f"Обнаружены неизвестные группы: {invalid_groups}"
        )

    checks.append({
        "check": "valid_groups",
        "status": status,
        "description": description
    })

    # =========================
    # 5. Valid conversion
    # =========================

    valid_conversion = {0, 1}
    actual_conversion = set(
        df["converted_observed"].dropna().unique()
    )

    invalid_conversion = actual_conversion - valid_conversion

    if not invalid_conversion:
        status = "PASS"
        description = "converted_observed содержит только 0 и 1"
    else:
        status = "FAIL"
        description = (
            "Обнаружены некорректные значения "
            f"converted_observed: {invalid_conversion}"
        )

    checks.append({
        "check": "valid_conversion",
        "status": status,
        "description": description
    })

    # =========================
    # 6. Group A not empty
    # =========================

    n_a = (df["group"] == "A").sum()

    if n_a > 0:
        status = "PASS"
        description = f"Группа A содержит {n_a} пользователей"
    else:
        status = "FAIL"
        description = "Группа A пустая"

    checks.append({
        "check": "group_a_not_empty",
        "status": status,
        "description": description
    })

    # =========================
    # 7. Group B not empty
    # =========================

    n_b = (df["group"] == "B").sum()

    if n_b > 0:
        status = "PASS"
        description = f"Группа B содержит {n_b} пользователей"
    else:
        status = "FAIL"
        description = "Группа B пустая"

    checks.append({
        "check": "group_b_not_empty",
        "status": status,
        "description": description
    })

    # =========================
    # 8. Sample Ratio Mismatch
    # =========================

    observed_a = (df["group"] == "A").sum()
    observed_b = (df["group"] == "B").sum()

    observed = [
        observed_a,
        observed_b
    ]

    total_users = observed_a + observed_b

    expected = [
        total_users * EXPECTED_GROUP_RATIO["A"],
        total_users * EXPECTED_GROUP_RATIO["B"]
    ]

    if total_users == 0 or observed_a == 0 or observed_b == 0:
        status = "FAIL"
        description = "Невозможно проверить SRM: одна из групп пуста"
        checks.append({
            "check": "sample_ratio_mismatch",
            "status": status,
            "description": description
        })
        quality_passed = False
        print("Проверки качества данных завершены: FAIL")
        return quality_passed, checks

    srm_stat, srm_p_value = chisquare(
        f_obs=observed,
        f_exp=expected
    )

    if srm_p_value >= SRM_ALPHA:
        status = "PASS"
        description = (
            f"Распределение A/B соответствует ожидаемому "
            f"{EXPECTED_GROUP_RATIO['A']:.0%}/"
            f"{EXPECTED_GROUP_RATIO['B']:.0%} "
            f"(p-value={srm_p_value:.4f})"
        )
    else:
        status = "FAIL"
        description = (
            f"Обнаружено отклонение распределения A/B "
            f"от ожидаемого "
            f"{EXPECTED_GROUP_RATIO['A']:.0%}/"
            f"{EXPECTED_GROUP_RATIO['B']:.0%} "
            f"(p-value={srm_p_value:.4f})"
        )

    checks.append({
        "check": "sample_ratio_mismatch",
        "status": status,
        "description": description
    })

    # =========================
    # Overall result
    # =========================

    quality_passed = all(
        check["status"] == "PASS"
        for check in checks
    )

    # =========================
    # Terminal output
    # =========================

    print("=== DATA QUALITY CHECKS ===")

    for check in checks:
        print(
            f"\n{check['status']}: "
            f"{check['description']}"
        )

    if quality_passed:
        print("\nDATA QUALITY: PASS")
    else:
        print("\nDATA QUALITY: FAIL")

    return quality_passed, checks