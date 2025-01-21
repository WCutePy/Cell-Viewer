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


def write_metadata(sheet, current_row, file_name, experiment_name,
                    amount_of_sites,
                   substance_names, substance_thresholds):
    metadata = f"""
    Original file name\t{file_name}
    Experiment name\t{experiment_name}
    Amount of sites\t{amount_of_sites}
    Substance thresholds:
    {"\n".join(f"{a}\t{b}" for a, b in zip(substance_names,
                                           substance_thresholds))}
    """
    current_row = write_multiline_to_sheet(sheet, metadata, current_row)
    
    return current_row + 2


def write_matrices(writer, sheet, current_row, matrix_explanations, matrices):
    for text, matrix in zip(matrix_explanations, matrices):
        current_row = write_line_to_sheet(sheet, text, current_row)
        
        matrix.to_excel(writer, index=True, sheet_name=sheet.title,
                        startrow=current_row - 1)
        current_row += matrix.shape[0] + 1 + 2
    return current_row


def write_individual_analysis_to_binary(
        file_name: str = None, experiment_name: str = None,
        amount_of_sites: int = None,
        substance_names: list[str] = None,
        substance_thresholds: list[float] = None,
        matrix_explanations: list[str] = None,
        matrices: list[pd.DataFrame] = None
):
    """
    Writes the content of an excell file
    using openpyxl as the engine, through
    pandas to Easily write the pandas dataframes to it.
    
    This writes the metadata first, followed up by the
    matrices that must be written into it.
    
    Everything is written to one sheet.
    It's possible to write in multiple sheets but that
    is currently not done.
    
    It dumps the content into latin1 format.
    This is so JavaScript can natively work with it.
    
    Args:
        file_name:
        experiment_name:
        amount_of_sites:
        substance_names:
        substance_thresholds:
        matrix_explanations:
        matrices:

    Returns:

    """
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
        
        current_row = write_metadata(sheet, current_row, file_name,
                                     experiment_name, amount_of_sites,
                                     substance_names,
                                     substance_thresholds)
        
        current_row = write_matrices(writer, sheet, current_row,
                                     matrix_explanations, matrices)
    
    excel_data = output.getvalue()
    excel_data = excel_data.decode("latin1")
    return excel_data


def write_comparison_analysis_to_binary(
        file_names:list[str]=None,
        experiment_names:list[str]=None,
        amount_of_sites:list[int]=None,
        substance_names:list[str]=None, substance_thresholds:list[str]=None,
        individual_matrix_explanations:list[str]=None,
        individual_matrices:list[pd.DataFrame]=None,
        matrix_explanations:list[str]=None,
        matrices:list[pd.DataFrame]=None
):
    
    """
    Writes out the
    
    Args:
        file_names:
        experiment_names:
        substance_names:
        substance_thresholds:
        individual_matrix_explanations:
        individual_matrices:
        matrix_explanations:
        matrices:

    Returns:

    """
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        workbook = writer.book
        sheet_name = "Sheet1"
        workbook.create_sheet(title=sheet_name)
        sheet = workbook[sheet_name]
        
        current_row = 1
        
        for file_name, experiment_name, sites, substance_name, substance_threshold, \
                ind_matrix_explanations, ind_matrices \
                in zip(file_names, experiment_names, amount_of_sites, substance_names,
                       substance_thresholds, individual_matrix_explanations,
                       individual_matrices):
                       
            current_row = write_metadata(sheet, current_row, file_name,
                                         experiment_name, sites,
                                         substance_name,
                                         substance_threshold)
            
            current_row = write_matrices(writer, sheet, current_row,
                                         ind_matrix_explanations, ind_matrices)
        
        current_row = write_line_to_sheet(sheet, "Aggregated comparison", current_row)
        
        current_row = write_matrices(writer, sheet, current_row,
                                     matrix_explanations, matrices)
    
    excel_data = output.getvalue()
    excel_data = excel_data.decode("latin1")
    return excel_data
