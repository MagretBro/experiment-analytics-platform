import pandas as pd


def save_ab_test_result(
    run_path,
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
    statistically_significant
):
    result = pd.DataFrame([
        {"metric": "n_a", "value": n_a},
        {"metric": "success_a", "value": success_a},
        {"metric": "conversion_a", "value": conversion_a},

        {"metric": "n_b", "value": n_b},
        {"metric": "success_b", "value": success_b},
        {"metric": "conversion_b", "value": conversion_b},

        {"metric": "absolute_uplift", "value": absolute_uplift},
        {"metric": "relative_uplift", "value": relative_uplift},

        {"metric": "z_statistic", "value": z_stat},
        {"metric": "p_value", "value": p_value},

        {"metric": "ci_lower", "value": ci_lower},
        {"metric": "ci_upper", "value": ci_upper},

        {"metric": "alpha", "value": alpha},
        {
            "metric": "statistically_significant",
            "value": statistically_significant
        }
    ])

    output_path = run_path / "result.csv"

    result.to_csv(
        output_path,
        index=False
    )

    return output_path