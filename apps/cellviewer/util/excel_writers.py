import pandas as pd
import io
from string import ascii_uppercase
from openpyxl.worksheet.worksheet import Worksheet


def write_line_to_sheet(sheet: Worksheet, line: str,
                        row: int = 1) -> int:
    for letter, value in zip(ascii_uppercase, line.lstrip().split("\t")):
        sheet[f"{letter}{row}"] = value
    return row + 1


def write_multiline_to_sheet(sheet: Worksheet, text: str,
                             start_row: int = 1) -> int:
    """
    Writes multiple lines to an openpyxl worksheet sheet.

    It strips white space from the whole string,
    and it left strips from each line. This is to make the string
    used look clearer within code.
    This might however not be preferred in the future, add
    some extra checks in that case.

    It returns the new current row index that should be empty.

    Args:
        sheet:
        text:
        start_row:

    Returns:

    """
    for row_index, line in enumerate(text.strip().split("\n"),
                                     start=start_row):
        write_line_to_sheet(sheet, line, row_index)
    return row_index + 1


def write_individual_analysis_to_binary(
        file_name: str = None, experiment_name: str = None,
        substance_names: list[str] = None,
        substance_thresholds: list[float] = None,
        matrix_explanations: list[str] = None,
        matrices: list[pd.DataFrame] = None
):
    output = io.BytesIO()
    
    if file_name is None:
        file_name = "unnamed"
    if experiment_name is None:
        experiment_name = file_name
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        workbook = writer.book
        sheet_name = "Sheet1"
        workbook.create_sheet(title=sheet_name)
        sheet = workbook[sheet_name]
        
        current_row = 1
        
        metadata = f"""
        Original file name\t{file_name}
        Experiment name\t{experiment_name}
        Substance thresholds:
        {"\n".join(f"{a}\t{b}" for a, b in zip(substance_names,
                                               substance_thresholds))}
        """
        current_row = write_multiline_to_sheet(sheet, metadata, current_row)
        
        current_row += 2
        
        for text, matrix in zip(matrix_explanations, matrices):
            current_row = write_line_to_sheet(sheet, text, current_row)
            
            matrix.to_excel(writer, index=True, sheet_name=sheet_name,
                            startrow=current_row - 1)
            current_row += matrix.shape[0] + 1 + 2
    
    excel_data = output.getvalue()
    excel_data = excel_data.decode("latin1")
    return excel_data
    

