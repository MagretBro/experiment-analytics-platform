import unittest
from unittest.mock import patch
import pandas as pd
from src.data_quality import run_data_quality_checks

class TestDataQuality(unittest.TestCase):
    """Проверки валидации данных перед анализом A/B-теста."""

    def setUp(self):
        """Подготавливает корректный тестовый датасет."""
        self.valid_df = pd.DataFrame({
            "user_id": [1, 2, 3, 4],
            "group": ["A", "A", "B", "B"],
            "converted_observed": [1, 0, 1, 0],
        })

    def run_checks(self, df):
        """Запускает проверки без вывода сообщений в консоль."""
        with patch("builtins.print"):
            return run_data_quality_checks(df)

    def get_check(self, checks, name):
        """Возвращает результат проверки по её названию."""
        return next(check for check in checks if check["check"] == name)

    def test_valid_dataset_passes(self):
        """Проверяет, что корректный датасет проходит все проверки."""
        passed, checks = self.run_checks(self.valid_df)
        self.assertTrue(passed)

    def test_empty_dataset_fails(self):
        """Проверяет, что пустой датасет отклоняется."""
        passed, checks = self.run_checks(pd.DataFrame())
        self.assertFalse(passed)
        self.assertEqual(
            self.get_check(checks, "non_empty_dataset")["status"], "FAIL"
        )

    def test_missing_columns_fail(self):
        """Проверяет наличие обязательных колонок."""
        passed, checks = self.run_checks(pd.DataFrame({"user_id": [1, 2]}))
        self.assertFalse(passed)
        self.assertEqual(
            self.get_check(checks, "required_columns")["status"], "FAIL"
        )

    def test_duplicate_user_id_fails(self):
        """Проверяет, что один пользователь не встречается несколько раз."""
        df = self.valid_df.copy()
        df.loc[1, "user_id"] = 1

        passed, checks = self.run_checks(df)

        self.assertFalse(passed)
        self.assertEqual(
            self.get_check(checks, "unique_user_id")["status"], "FAIL"
        )

    def test_invalid_conversion_value_fails(self):
        """Проверяет, что конверсия содержит только значения 0 и 1."""
        df = self.valid_df.copy()
        df.loc[1, "converted_observed"] = 2

        passed, checks = self.run_checks(df)

        self.assertFalse(passed)
        self.assertEqual(
            self.get_check(checks, "valid_conversion")["status"], "FAIL"
        )

    def test_missing_values_fail(self):
        """Проверяет, что в обязательных полях нет пропусков."""
        df = self.valid_df.copy()
        df.loc[0, "converted_observed"] = None

        passed, checks = self.run_checks(df)

        self.assertFalse(passed)
        self.assertEqual(
            self.get_check(checks, "missing_values")["status"], "FAIL"
        )

    def test_invalid_group_fails(self):
        """Проверяет, что используются только группы A и B."""
        df = self.valid_df.copy()
        df.loc[0, "group"] = "C"

        passed, checks = self.run_checks(df)

        self.assertFalse(passed)
        self.assertEqual(
            self.get_check(checks, "valid_groups")["status"], "FAIL"
        )

    def test_missing_experiment_group_fails(self):
        """Проверяет, что в эксперименте присутствуют обе группы."""
        df = self.valid_df[self.valid_df["group"] == "A"].copy()

        passed, checks = self.run_checks(df)

        self.assertFalse(passed)
        self.assertEqual(
            self.get_check(checks, "sample_ratio_mismatch")["status"], "FAIL"
        )

    def test_sample_ratio_mismatch_fails(self):
        """Проверяет выявление сильного отклонения от пропорции 50/50."""
        df = pd.DataFrame({
            "user_id": range(100),
            "group": ["A"] * 90 + ["B"] * 10,
            "converted_observed": [0, 1] * 50,
        })

        passed, checks = self.run_checks(df)

        self.assertFalse(passed)
        self.assertEqual(
            self.get_check(checks, "sample_ratio_mismatch")["status"], "FAIL"
        )

    def test_user_in_both_groups_fails(self):
        """Проверяет, что один пользователь не попал в группы A и B."""
        df = pd.concat([
            self.valid_df,
            pd.DataFrame({
                "user_id": [1],
                "group": ["B"],
                "converted_observed": [1],
            }),
        ], ignore_index=True)

        passed, checks = self.run_checks(df)

        self.assertFalse(passed)
        self.assertEqual(
            self.get_check(checks, "unique_user_id")["status"], "FAIL"
        )    

if __name__ == "__main__":
    unittest.main()
