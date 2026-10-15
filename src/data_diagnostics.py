
import pandas as pd


def diagnose_dataset(
    df: pd.DataFrame,
    metric_column: str = "converted_observed",
    group_column: str = "group",
    id_column: str = "user_id",
) -> pd.DataFrame:
    """
    Исследовательская диагностика общего датасета и групп A/B.
    Пока поддерживает бинарную и числовую метрики.
    Возвращает таблицу диагностических результатов.
    """

    rows = []

    def add(scope, category, name, value, status="INFO", comment=""):
        rows.append({
            "scope": scope,
            "category": category,
            "check": name,
            "value": value,
            "status": status,
            "comment": comment,
        })

    # 1. Общая информация
    add("ALL", "structure", "row_count", len(df))
    add("ALL", "structure", "column_count", len(df.columns))
    add("ALL", "structure", "columns", ", ".join(map(str, df.columns)))

    if df.empty:
        add(
            "ALL", "data_quality", "empty_dataset", True,
            "ERROR", "Датасет пуст. Анализ невозможен."
        )
        return pd.DataFrame(rows)

    # 2. Типы столбцов
    for column in df.columns:
        add(
            "ALL", "structure", f"dtype:{column}",
            str(df[column].dtype)
        )

    # 3. Пропуски
    for column in df.columns:
        missing_count = int(df[column].isna().sum())
        missing_pct = missing_count / len(df)

        add(
            "ALL", "data_quality", f"missing:{column}",
            f"{missing_count} ({missing_pct:.2%})",
            "WARNING" if missing_count else "PASS",
            "Есть пропуски" if missing_count else "Пропусков нет"
        )

    # 4. Дубликаты идентификаторов
    if id_column in df.columns:
        duplicate_count = int(
            df[id_column].duplicated().sum()
        )
        add(
            "ALL", "data_quality", "duplicate_ids",
            duplicate_count,
            "WARNING" if duplicate_count else "PASS",
            "Проверь единицу анализа и повторные записи"
            if duplicate_count else "Повторных ID нет"
        )

    # 5. Оценка метрики
    if metric_column not in df.columns:
        add(
            "ALL", "metric", "metric_exists", False,
            "ERROR", f"Нет столбца {metric_column}"
        )
        return pd.DataFrame(rows)

    metric = pd.to_numeric(df[metric_column], errors="coerce")
    invalid_count = int(
        (df[metric_column].notna() & metric.isna()).sum()
    )
    add(
        "ALL", "metric", "non_numeric_values", invalid_count,
        "WARNING" if invalid_count else "PASS",
        "Значения не удалось преобразовать в числа"
        if invalid_count else "Все непустые значения числовые"
    )

    valid_metric = metric.dropna()

    if valid_metric.empty:
        add(
            "ALL", "metric", "metric_has_values", False,
            "ERROR", "Нет пригодных значений метрики"
        )
        return pd.DataFrame(rows)

    # Бинарная метрика: распределение 0/1 и конверсия
    is_binary = valid_metric.isin([0, 1]).all()

    if is_binary:
        counts = valid_metric.value_counts()

        add("ALL", "metric", "metric_type", "binary")
        add("ALL", "metric", "zeros", int(counts.get(0, 0)))
        add("ALL", "metric", "ones", int(counts.get(1, 0)))
        add(
            "ALL", "metric", "conversion",
            float(valid_metric.mean()),
            comment="Доля единиц среди непустых значений"
        )
    else:
        add("ALL", "metric", "metric_type", "numeric")

        stats = valid_metric.describe(
            percentiles=[0.25, 0.5, 0.75, 0.90, 0.95, 0.99]
        )

        for stat_name, stat_value in stats.items():
            add(
                "ALL", "distribution", stat_name,
                float(stat_value)
            )

        add(
            "ALL", "distribution", "skewness",
            float(valid_metric.skew()),
            comment="Асимметрия распределения; не тест нормальности"
        )

        q1 = valid_metric.quantile(0.25)
        q3 = valid_metric.quantile(0.75)
        iqr = q3 - q1
        outliers = (
            (valid_metric < q1 - 1.5 * iqr)
            | (valid_metric > q3 + 1.5 * iqr)
        )

        add(
            "ALL", "distribution", "potential_outliers",
            int(outliers.sum()),
            comment="Выбросы по правилу 1.5 × IQR; требуют проверки"
        )

    # 6. Отдельная диагностика каждой группы
    if group_column not in df.columns:
        add(
            "ALL", "groups", "group_column_exists", False,
            "ERROR", f"Нет столбца {group_column}"
        )
        return pd.DataFrame(rows)

    for group_name, group_df in df.groupby(
        group_column, dropna=False
    ):
        scope = str(group_name)
        group_metric = pd.to_numeric(
            group_df[metric_column], errors="coerce"
        ).dropna()

        add(scope, "sample", "rows", len(group_df))

        if id_column in group_df.columns:
            add(
                scope, "sample", "unique_ids",
                int(group_df[id_column].nunique())
            )

        add(
            scope, "metric", "valid_metric_values",
            len(group_metric)
        )

        if group_metric.empty:
            add(
                scope, "metric", "metric_available", False,
                "ERROR", "Нет пригодных значений метрики"
            )
            continue

        if group_metric.isin([0, 1]).all():
            counts = group_metric.value_counts()
            add(scope, "metric", "metric_type", "binary")
            add(scope, "metric", "zeros", int(counts.get(0, 0)))
            add(scope, "metric", "ones", int(counts.get(1, 0)))
            add(
                scope, "metric", "conversion",
                float(group_metric.mean())
            )
        else:
            stats = group_metric.describe(
                percentiles=[0.25, 0.5, 0.75, 0.90, 0.95, 0.99]
            )

            for stat_name, stat_value in stats.items():
                add(
                    scope, "distribution", stat_name,
                    float(stat_value)
                )

            add(
                scope, "distribution", "skewness",
                float(group_metric.skew())
            )

    return pd.DataFrame(rows)
