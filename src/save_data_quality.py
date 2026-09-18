import pandas as pd


def save_data_quality_results(run_path, checks):
    """
    Сохраняет результаты Data Quality checks в CSV.

    checks:
        список словарей вида:
        {
            "check": "required_columns",
            "status": "PASS",
            "description": "Все необходимые колонки присутствуют"
        }
    """

    quality_df = pd.DataFrame(checks)

    output_path = run_path / "data_quality.csv"

    quality_df.to_csv(
        output_path,
        index=False
    )

    return output_path