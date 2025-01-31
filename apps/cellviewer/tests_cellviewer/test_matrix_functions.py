from unittest import TestCase
import pandas as pd
from apps.cellviewer.util.matrix_functions import *


class TestMatrixFunctions(TestCase):
    
    def test_filtered_polars_dataframe_two_values(self):
        df = pl.DataFrame({
            "Well": ["B02", "B02", "B02"],
            "Site": [1, 1, 1],
            "Cell": [1, 2, 3],
            "OCT4": [2.7, 3.5, 2.5],
            "SOX17": [2.9, 3.4, 2.7]
        })
        
        result = filtered_polars_dataframe(df, [2.5, 2.8])
        
        assert result.shape[0] == 2, \
            f"Expected 2 rows, but got {result.shape[0]}"
        result_oct4 = [2.7, 3.5]
        assert result["OCT4"].to_list() == result_oct4, \
            f"Expected filtered OCT4 values to be {result_oct4}"
        result_sox = [2.9, 3.4]
        assert result["SOX17"].to_list() == result_sox, \
            f"Expected filtered SOX17 values to be {result_sox}"
    
    def test_filtered_polars_dataframe_three_values(self):
        df = pl.DataFrame({
            "Well": ["B02", "B02", "B02"],
            "Site": [1, 1, 1],
            "Cell": [1, 2, 3],
            "OCT4": [2.7, 3.5, 2.5],
            "SOX17": [2.9, 3.4, 3.0],
            "THIRD": [3.1, 3.0, 2.3]
        })
        
        result = filtered_polars_dataframe(df, [2.51, 2.9, 3.01])
        
        assert result.shape[0] == 1, \
            f"Expected 1 rows, but got {result.shape[0]}"
        result_oct4 = [2.7]
        assert result["OCT4"].to_list() == result_oct4, \
            f"Expected filtered OCT4 values to be {result_oct4}"
        result_sox = [2.9]
        assert result["SOX17"].to_list() == result_sox, \
            f"Expected filtered SOX17 values to be {result_sox}"
        result_third = [3.1]
        assert result["THIRD"].to_list() == result_third, \
            f"Expected filtered SOX17 values to be {result_third}"
    
    def test_filtered_polars_dataframe_filter_out_all(self):
        df = pl.DataFrame({
            "Well": ["B02", "B02", "B02"],
            "Site": [1, 1, 1],
            "Cell": [1, 2, 3],
            "OCT4": [2.7, 3.5, 2.5],
        })
        
        result = filtered_polars_dataframe(df, [4])
        assert result.shape[0] == 0
    
    def test_calculate_well_count_matrix_returns_pandas(self):
        """
        The well count matrix calculation is used all over
        the code base, and the code base expects it to
        output a pandas dataframe. Changing the output type,
        might require changing all the code that depends on
        this.
        """
        df = pl.DataFrame({
            "Well": ["B02", "B02", "B02", "C02", "C02"]
        })
        
        result = calculate_well_count_matrix(df)
        assert pd.DataFrame == type(result), \
            "Why did you change the type?"
    
    def test_calculate_well_count_matrix_correct_counting(self):
        """
        The output of calculate_well_count_matrix has a specific
        format as a result of the original implementation.
        This format might or might not be necessary to be
        maintained, but is maintained by the current tests.
        
        The datatype is ignored in this, as pandas sometimes dynamically
        chooses datatypes. What matters is
        Returns:

        """
        df = pl.DataFrame({
            "Well": ["B02", "B02", "B02", "C02", "C02"]
        })
        
        result = calculate_well_count_matrix(df)
        
        expected_result = pd.DataFrame({
            "02": [3, 2],
        }, index=["B", "C"]).rename_axis(index="row", columns="cols")
        
        assert result.map(lambda x: isinstance(x, int)).all().all(), \
            "Not all values are integers"
        
        pd.testing.assert_frame_equal(
            result, expected_result, check_dtype=False
        )
    
    def test_calculate_well_count_matrix_missing_wells_are_zero(self):
        """
        This tests to see that if a well is missing, The output
        will still be rectangular and the count of the well
        will be zero.

        """
        df = pl.DataFrame({
            "Well": ["B02", "C03"]
        })
        
        result = calculate_well_count_matrix(df)
        
        expected_result = pd.DataFrame({
            "02": [1, 0],
            "03": [0, 1],
        }, index=["B", "C"]).rename_axis(index="row", columns="cols")
        
        pd.testing.assert_frame_equal(
            result, expected_result, check_dtype=False
        )
    
    def test_calculate_well_count_percent_correct_calculation(self):
        """

        """
        df = pd.DataFrame({
            "02": [11, 400],
        }, index=["B", "C"]).rename_axis(index="row", columns="cols")
        
        df_filtered = pd.DataFrame({
            "02": [7, 300],
        }, index=["B", "C"]).rename_axis(index="row", columns="cols")
        
        result = calculate_well_count_percent(df, df_filtered)
        
        expected_result = pd.DataFrame({
            "02": [7 / 11 * 100, 300 / 400 * 100],
        }, index=["B", "C"]).rename_axis(index="row", columns="cols")
        
        pd.testing.assert_frame_equal(
            result, expected_result, check_dtype=False
        )
    
    def test_calculate_well_count_percent_handle_zero_division(self):
        """

        """
        df = pd.DataFrame({
            "02": [100, 0],
        }, index=["B", "C"]).rename_axis(index="row", columns="cols")
        
        df_filtered = pd.DataFrame({
            "02": [0, 0],
        }, index=["B", "C"]).rename_axis(index="row", columns="cols")
        
        result = calculate_well_count_percent(df, df_filtered)
        
        expected_result = pd.DataFrame({
            "02": [0, 0],
        }, index=["B", "C"]).rename_axis(index="row", columns="cols")
        
        pd.testing.assert_frame_equal(
            result, expected_result, check_dtype=False
        )
    
    def test_calculate_well_counts_and_percent(self):
        """
        Checks if the function performing multiple of the tested
        tasks properly uses the functions it is supposed to use
        and returns the proper information.
        
        The individual behaviour of the functions should not be
        tested here
        Returns:

        """
        df = pl.DataFrame({
            "Well": ["B02", "B02", "B02"],
            "Site": [1, 1, 1],
            "Cell": [1, 2, 3],
            "OCT4": [0, 2, 2]
        })
        
        expected_well_count_matrix = pd.DataFrame({
            "02": [3],
        }, index=["B"]).rename_axis(index="row", columns="cols")
        
        expected_filtered_well_count_matrix = pd.DataFrame({
            "02": [2],
        }, index=["B"]).rename_axis(index="row", columns="cols")
        
        expected_well_count_matrix_percent = pd.DataFrame({
            "02": [2 / 3 * 100],
        }, index=["B"]).rename_axis(index="row", columns="cols")
        
        well_count_matrix, filtered_well_count_matrix, \
            well_count_matrix_percent = calculate_well_counts_and_percent(
            df, [1])
        
        pd.testing.assert_frame_equal(
            well_count_matrix, expected_well_count_matrix, check_dtype=False
        )
        
        pd.testing.assert_frame_equal(
            filtered_well_count_matrix, expected_filtered_well_count_matrix,
            check_dtype=False
        )
        
        pd.testing.assert_frame_equal(
            well_count_matrix_percent, expected_well_count_matrix_percent,
            check_dtype=False
        )
    
    def test_calculate_well_counts_and_percent_retain_wells_on_aggressive_filtering(self):
        """
        Tests that if the thresholds would filter out all the entries
        on all wells, or even only on a few wells, the filtered
        matrix will still retain each well with a zero
        
        This is important as the visualization requires this to
        be consistent.
        """
        df = pl.DataFrame({
            "Well": ["B02", "C02", "B03", "C03"],
            "Site": [1, 1, 1, 1],
            "Cell": [1, 2, 3, 4],
            "OCT4": [0, 0, 0, 0]
        })
        
        expected_filtered_well_count_matrix = pd.DataFrame({
            "02": [0, 0],
            "03": [0, 0]
        }, index=["B", "C"]).rename_axis(index="row", columns="cols")
        
        _, filtered_well_count_matrix, _ = \
            calculate_well_counts_and_percent(df, [1])
        
        pd.testing.assert_frame_equal(
            filtered_well_count_matrix,
            expected_filtered_well_count_matrix,
            check_dtype=False
        )
    
    def test_calculate_mean_across_each_well_positive_values(self):
        """
        Also tests that rename axis is preserved through the
        function. This could be a separate test, but also would
        add even more duplication to the tests that already exists.
        Returns:

        """
        matrix_a = pd.DataFrame({
            1: [20, 60],
            2: [40, 80]
        }, index=["A", "B"]).rename_axis(index="row", columns="cols")
        
        matrix_b = pd.DataFrame({
            1: [30, 50],
            2: [0, 10]
        }, index=["A", "B"]).rename_axis(index="row", columns="cols")
        
        expected_result = pd.DataFrame({
            1: [25, 55],
            2: [20, 45]
        }, index=["A", "B"], dtype="float64").rename_axis(index="row",
                                                          columns="cols")
        
        result = calculate_mean_across_each_well([matrix_a, matrix_b])
        pd.testing.assert_frame_equal(result, expected_result)
    
    def test_calculate_mean_across_each_well_zeros(self):
        matrix_a = pd.DataFrame({
            1: [0, 0],
            2: [0, 0]
        }, index=["A", "B"])
        
        matrix_b = pd.DataFrame({
            1: [0, 0],
            2: [0, 0]
        }, index=["A", "B"])
        
        expected_result = pd.DataFrame({
            1: [0, 0],
            2: [0, 0]
        }, index=["A", "B"], dtype="float64")
        
        result = calculate_mean_across_each_well([matrix_a, matrix_b])
        pd.testing.assert_frame_equal(result, expected_result)
    
    def test_calculate_standard_deviation_across_each_well(self):
        """
        Tests if the result of the calculation is correct.
        
        It manually writes out the calculation, to be sure
        The implemented formula, matches up the intended calculation.
        Returns:

        """
        matrix_a = pd.DataFrame({
            1: [3, 5]
        }, index=["A", "B"])
        
        matrix_b = pd.DataFrame({
            1: [7, 6]
        }, index=["A", "B"])
        
        matrix_mean = pd.DataFrame({
            1: [5, 5.5]
        }, index=["A", "B"])
        
        expected_result = pd.DataFrame({
            1: [(((3 - 5) ** 2 + (7 - 5) ** 2) / 2) ** 0.5,
                ((0.25 + 0.25) / 2) ** 0.5]
        }, index=["A", "B"], dtype="float64")
        # 1 : [2.0, 0.5]
        
        result = calculate_standard_deviation_across_each_well(
            [matrix_a, matrix_b], matrix_mean)
        
        pd.testing.assert_frame_equal(result, expected_result)
    
    def test_calculate_standard_deviation_across_each_well_realistic_example(
            self):
        """
        Tests if the result of the calculation is correct.

        It manually writes out the calculation, to be sure
        The implemented formula, matches up the intended calculation.
        
        Seems to be correct in a realistic situation.
        Returns:
        """
        
        val_a, val_b = 88.6677956534011, 100
        avg = (val_a + val_b) / 2
        std = (((val_a - avg) ** 2 + (val_b - avg) ** 2) / 2) ** 0.5
        # std = 5.666102
        matrix_a = pd.DataFrame({
            1: [val_a]
        }, index=["A"])
        
        matrix_b = pd.DataFrame({
            1: [val_b]
        }, index=["A"])
        
        matrix_mean = pd.DataFrame({
            1: [avg]
        }, index=["A"])
        
        expected_result = pd.DataFrame({
            1: [std]
        }, index=["A"], dtype="float64")
        # 1 : [2.0, 0.5]
        
        result = calculate_standard_deviation_across_each_well(
            [matrix_a, matrix_b], matrix_mean)
        
        pd.testing.assert_frame_equal(result, expected_result)
    
    def test_calculate_standard_deviation_across_each_well_all_zeros(self):
        matrix_a = pd.DataFrame({
            1: [0, 0]
        }, index=["A", "B"])
        
        matrix_b = pd.DataFrame({
            1: [0, 0]
        }, index=["A", "B"])
        
        matrix_mean = pd.DataFrame({
            1: [0, 0]
        }, index=["A", "B"])
        
        expected_result = pd.DataFrame({
            1: [0, 0]
        }, index=["A", "B"], dtype="float64")
        
        result = calculate_standard_deviation_across_each_well(
            [matrix_a, matrix_b], matrix_mean)
        
        pd.testing.assert_frame_equal(result, expected_result)
