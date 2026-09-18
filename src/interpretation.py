from pathlib import Path


def format_percentage(value):
    return f"{value:.2%}"


def format_percentage_points(value):
    return f"{value:.2%}"


def generate_interpretation(
    run_id,
    n_a,
    success_a,
    conversion_a,
    n_b,
    success_b,
    conversion_b,
    absolute_uplift,
    relative_uplift,
    z_stat,
    p_value,
    ci_lower,
    ci_upper,
    alpha
):
    lines = []

    # =========================
    # Header
    # =========================

    lines.append("A/B TEST REPORT")
    lines.append("=" * 40)
    lines.append("")

    lines.append(f"RUN ID: {run_id}")
    lines.append("")

    # =========================
    # Sample
    # =========================

    lines.append("SAMPLE")
    lines.append("-" * 40)

    lines.append(
        f"Группа A: {n_a} пользователей, "
        f"{success_a} конверсий"
    )

    lines.append(
        f"Группа B: {n_b} пользователей, "
        f"{success_b} конверсий"
    )

    lines.append("")

    # =========================
    # Conversion
    # =========================

    lines.append("CONVERSION")
    lines.append("-" * 40)

    lines.append(
        f"Конверсия A: {format_percentage(conversion_a)}"
    )

    lines.append(
        f"Конверсия B: {format_percentage(conversion_b)}"
    )

    lines.append("")

    # =========================
    # Observed effect
    # =========================

    lines.append("OBSERVED EFFECT")
    lines.append("-" * 40)

    if absolute_uplift > 0:
        lines.append(
            f"Наблюдаемая конверсия группы B выше группы A "
            f"на {format_percentage_points(absolute_uplift)}."
        )

    elif absolute_uplift < 0:
        lines.append(
            f"Наблюдаемая конверсия группы A выше группы B "
            f"на {format_percentage_points(abs(absolute_uplift))}."
        )

    else:
        lines.append(
            "Наблюдаемая конверсия групп A и B одинаковая."
        )

    lines.append(
        f"Absolute uplift (B - A): "
        f"{format_percentage(absolute_uplift)}"
    )

    lines.append(
        f"Relative uplift: "
        f"{format_percentage(relative_uplift)}"
    )

    lines.append("")

    # =========================
    # Statistics
    # =========================

    lines.append("STATISTICAL TEST")
    lines.append("-" * 40)

    lines.append(
        f"Z-statistic: {z_stat:.3f}"
    )

    lines.append(
        f"P-value: {p_value:.4f}"
    )

    lines.append(
        f"Alpha: {alpha}"
    )

    lines.append("")

    # =========================
    # Interpretation of p-value
    # =========================

    if p_value < alpha:

        lines.append(
            f"p-value ({p_value:.4f}) меньше "
            f"уровня значимости α = {alpha}."
        )

        lines.append(
            "Статистически значимая разница между "
            "группами обнаружена."
        )

        lines.append(
            "Нулевая гипотеза отвергается "
            "на выбранном уровне значимости."
        )

    else:

        lines.append(
            f"p-value ({p_value:.4f}) больше "
            f"уровня значимости α = {alpha}."
        )

        lines.append(
            "Статистически значимой разницы между "
            "группами не обнаружено."
        )

        lines.append(
            "Недостаточно оснований утверждать, "
            "что наблюдаемая разница обусловлена "
            "эффектом варианта."
        )

    lines.append("")

    # =========================
    # Confidence interval
    # =========================

    lines.append("CONFIDENCE INTERVAL")
    lines.append("-" * 40)

    lines.append(
        f"95% CI for difference: "
        f"[{format_percentage(ci_lower)}; "
        f"{format_percentage(ci_upper)}]"
    )

    lines.append("")

    if ci_lower <= 0 <= ci_upper:

        lines.append(
            "Доверительный интервал включает 0."
        )

        lines.append(
            "Это согласуется с отсутствием "
            "статистически значимого различия."
        )

    else:

        lines.append(
            "Доверительный интервал не включает 0."
        )

        lines.append(
            "Это согласуется с наличием "
            "статистически значимого различия."
        )

    lines.append("")

    return "\n".join(lines)


def save_interpretation(
    run_path,
    report
):
    output_path = Path(run_path) / "summary.txt"

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(report)

    return output_path