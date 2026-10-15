from pathlib import Path


# =========================
# Форматирование
# =========================

def fmt_pct(value, digits=2):
    """0.0525 -> '5.25%'"""
    return f"{value * 100:.{digits}f}%"


def fmt_pp(value, digits=2):
    """0.002 -> '+0.20 п.п.'"""
    sign = "+" if value >= 0 else "−"
    return f"{sign}{abs(value) * 100:.{digits}f} п.п."


def fmt_signed_pct(value, digits=2):
    """0.038 -> '+3.81%'"""
    sign = "+" if value >= 0 else "−"
    return f"{sign}{abs(value) * 100:.{digits}f}%"


def fmt_num(value, digits=3):
    return f"{value:.{digits}f}"


def verdict(p_value, alpha, ci_lower, ci_upper, absolute_uplift):
    """Возвращает человеческий вердикт."""
    significant = p_value < alpha
    ci_crosses_zero = ci_lower <= 0 <= ci_upper

    if not significant:
        return (
            "НЕТ СТАТИСТИЧЕСКИ ЗНАЧИМОЙ РАЗНИЦЫ",
            "Разница между группами может быть случайной. "
            "Недостаточно оснований, чтобы отдать предпочтение варианту B."
        )

    if absolute_uplift > 0:
        return (
            "ВАРИАНТ B ЛУЧШЕ",
            "Разница статистически значима и в пользу B. "
            "Есть основания катить вариант B на всю аудиторию."
        )

    return (
        "ВАРИАНТ B ХУЖЕ",
        "Разница статистически значима, но в пользу A. "
        "Вариант B запускать не стоит."
    )


# =========================
# Генерация отчёта
# =========================

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
    alpha,
):
    lines = []

    title, action = verdict(p_value, alpha, ci_lower, ci_upper, absolute_uplift)

    # --------------------------------------------------
    # Заголовок
    # --------------------------------------------------
    lines.append("=" * 60)
    lines.append("ОТЧЁТ ОБ A/B-ТЕСТЕ")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Запуск:        {run_id}")
    lines.append(f"Уровень значимости α = {alpha}")
    lines.append("")

    # --------------------------------------------------
    # Что сравнивали
    # --------------------------------------------------
    lines.append("-" * 60)
    lines.append("ЧТО СРАВНИВАЛИ")
    lines.append("-" * 60)
    lines.append("")
    lines.append("Группа A — контрольная (то, что было).")
    lines.append("Группа B — тестовая (новый вариант).")
    lines.append("Метрика — конверсия: доля пользователей, совершивших целевое действие.")
    lines.append("")

    # --------------------------------------------------
    # Размер выборки
    # --------------------------------------------------
    lines.append("-" * 60)
    lines.append("СКОЛЬКО ПОЛЬЗОВАТЕЛЕЙ")
    lines.append("-" * 60)
    lines.append("")
    lines.append(f"  Группа A:  {n_a:,} чел.,  из них конвертировались: {success_a:,}")
    lines.append(f"  Группа B:  {n_b:,} чел.,  из них конвертировались: {success_b:,}")
    lines.append(f"  Всего:     {n_a + n_b:,} чел.")
    lines.append("")

    # --------------------------------------------------
    # Конверсии
    # --------------------------------------------------
    lines.append("-" * 60)
    lines.append("КОНВЕРСИЯ")
    lines.append("-" * 60)
    lines.append("")
    lines.append(f"  Группа A:  {fmt_pct(conversion_a)}")
    lines.append(f"  Группа B:  {fmt_pct(conversion_b)}")
    lines.append("")

    # --------------------------------------------------
    # Эффект
    # --------------------------------------------------
    lines.append("-" * 60)
    lines.append("ЭФФЕКТ ОТ ВНЕДРЕНИЯ ВАРИАНТА B")
    lines.append("-" * 60)
    lines.append("")

    if absolute_uplift > 0:
        lines.append(
            f"  Конверсия в B ВЫШЕ, чем в A, "
            f"на {fmt_pp(absolute_uplift)} (абсолютный прирост)."
        )
    elif absolute_uplift < 0:
        lines.append(
            f"  Конверсия в B НИЖЕ, чем в A, "
            f"на {fmt_pp(absolute_uplift)} (абсолютное падение)."
        )
    else:
        lines.append("  Конверсия в A и B одинаковая.")

    lines.append("")
    lines.append(f"  Абсолютный прирост (B − A):  {fmt_pp(absolute_uplift)}")
    lines.append(f"  Относительный прирост:       {fmt_signed_pct(relative_uplift)}")
    lines.append("")
    lines.append("  Что это значит:")
    lines.append(
        "    • абсолютный прирост — на сколько процентных пунктов "
        "конверсия B больше конверсии A;"
    )
    lines.append(
        "    • относительный прирост — на сколько процентов "
        "изменилась конверсия относительно A."
    )
    lines.append("")

    # --------------------------------------------------
    # Статистика
    # --------------------------------------------------
    lines.append("-" * 60)
    lines.append("СТАТИСТИЧЕСКАЯ ПРОВЕРКА")
    lines.append("-" * 60)
    lines.append("")
    lines.append(f"  Z-статистика:  {fmt_num(z_stat)}")
    lines.append(f"  p-value:       {fmt_num(p_value, 4)}")
    lines.append(f"  α (порог):     {alpha}")
    lines.append("")

    if p_value < alpha:
        lines.append(
            f"  p-value ({fmt_num(p_value, 4)}) < α ({alpha}) — "
            "разница статистически значима."
        )
    else:
        lines.append(
            f"  p-value ({fmt_num(p_value, 4)}) ≥ α ({alpha}) — "
            "разница статистически НЕ значима."
        )
    lines.append("")

    # --------------------------------------------------
    # Доверительный интервал
    # --------------------------------------------------
    lines.append("-" * 60)
    lines.append("95% ДОВЕРИТЕЛЬНЫЙ ИНТЕРВАЛ ДЛЯ РАЗНИЦЫ (B − A)")
    lines.append("-" * 60)
    lines.append("")
    lines.append(f"  [{fmt_pp(ci_lower)} ; {fmt_pp(ci_upper)}]")
    lines.append("")

    if ci_lower <= 0 <= ci_upper:
        lines.append(
            "  Интервал накрывает 0 — значит, реальная разница может быть "
            "нулевой. Это согласуется с отсутствием значимости."
        )
    else:
        lines.append(
            "  Интервал не накрывает 0 — значит, реальная разница, скорее "
            "всего, не равна нулю. Это согласуется со значимым результатом."
        )
    lines.append("")

    # --------------------------------------------------
    # Вердикт
    # --------------------------------------------------
    lines.append("=" * 60)
    lines.append("ИТОГ")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"  {title}")
    lines.append("")
    lines.append(f"  {action}")
    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


# =========================
# Сохранение
# =========================

def save_interpretation(run_path, report):
    output_path = Path(run_path) / "summary.txt"
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(report)
    return output_path