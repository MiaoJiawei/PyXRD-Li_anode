import os
import numpy as np
from openpyxl import Workbook
from data_reader import get_reader
from data_processor import correct_ka2
from data_processor import fit_data
from data_processor import fit_peak
from data_processor import calculate_fwhm_spv

# Pushback peak curve to workbook
def pushpack_peak(worksheet, cont, col_index, start_row=3):
    j = start_row
    for cell in cont:
        worksheet.cell(j, col_index).value = float(cell) if cell is not None else None
        j += 1
    return worksheet

if __name__ == "__main__":
    # Select file type
    file_type = input("请选择文件类型（1: .rd, 2: .xrdml）: ").strip()
    peak_output = input("是否输出拟合结果（1: Yes, 2: No）: ").strip()
    reader = get_reader(file_type)

    # Get file list
    file_list = []
    for root, _, files in os.walk('.'):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if (file_type == "1" and ext == ".rd") or (file_type == "2" and ext == ".xrdml"):
                file_list.append(os.path.join(root, f))

    # Initialize the table
    wb = Workbook()
    ws_res = wb.active
    ws_res.title = 'Sample list'
    ws_res.freeze_panes = 'A2'
    ws_res.cell(1, 1).value = 'Sample Name'
    ws_res.cell(1, 2).value = 'D002 (Å)'
    ws_res.cell(1, 3).value = 'G%'
    ws_res.cell(1, 4).value = 'Graphite D002 Peak (deg)'
    ws_res.cell(1, 5).value = 'Graphite D002 FWHM (deg)'
    ws_res.cell(1, 6).value = 'Silicon D111 Peak (deg)'
    ws_res.cell(1, 7).value = 'Silicon D111 FWHM (deg)'
    if peak_output == "1":
        ws_res.cell(1, 7).value = 'Graphite D002 FWHM NET.(deg)'

    # Initialize parameters
    sam_list = []
    sam_index = 1

    # Data process
    for file_path in file_list:
        sample_name = os.path.splitext(file_path)[0]
        sam_list.append(sample_name)
        sam_index += 1
        try:
            scan_x, scan_y = reader.read_data(file_path)
            if scan_x is not None:
                corrected_x, corrected_y = correct_ka2(scan_x, scan_y)
                popt = fit_data(corrected_x, corrected_y)
                if popt is not None:
                    ws_res.cell(sam_index, 1).value = sample_name.split("\\")[-1]  # Sample name (use 'sample_name' for file path)
                    ws_res.cell(sam_index, 2).value = d_002 = 1.54056/(2*np.sin(np.radians((28.443 - popt[6] + popt[1])/2)))  # Graphite D002 value
                    ws_res.cell(sam_index, 3).value = 100 * (3.440 - d_002)/(3.440 - 3.354)
                    #ws_res.cell(sam_index, 2).value = -0.1302 * (28.443 - popt[6] + popt[1]) + 6.8127  # Graphite D002 value
                    ws_res.cell(sam_index, 4).value = popt[1]  # Graphite D002 peak position
                    ws_res.cell(sam_index, 5).value = calculate_fwhm_spv(popt[2], popt[3], popt[4])
                    ws_res.cell(sam_index, 6).value = popt[6]  # Silicon D111 peak position
                    ws_res.cell(sam_index, 7).value = calculate_fwhm_spv(popt[7], popt[8], popt[9])
                    if peak_output == "1":
                        # Create worksheet
                        ws_raw = wb.create_sheet(sample_name.split("\\")[-1])
                        ws_raw.freeze_panes = 'A3'
                        ws_raw.cell(2, 1).value = '2-Theta (deg)'
                        ws_raw.cell(2, 2).value = 'Intensity (A.U.)'
                        ws_raw.cell(2, 3).value = 'Corrected Intensity'
                        ws_raw.cell(2, 4).value = 'Fitted Curve'
                        ws_raw.cell(2, 5).value = 'Fitted Background'
                        ws_raw.cell(2, 6).value = 'Graphite D002 Peak'
                        ws_raw.cell(2, 7).value = 'Silicon D111 Peak'
                        ws_raw.cell(1, 1).value = 'Back'
                        ws_raw.cell(1, 1).hyperlink = "#'Sample list'!A%s" % str(sam_index)
                        # Calculate peak curves
                        fitted_curve, background, graphite_peak, silicon_peak, fwhm_gn = fit_peak(corrected_x, popt)
                        # Pushback peak curves
                        ws_raw = pushpack_peak(ws_raw, corrected_x, 1)
                        ws_raw = pushpack_peak(ws_raw, scan_y, 2)
                        ws_raw = pushpack_peak(ws_raw, corrected_y, 3)
                        ws_raw = pushpack_peak(ws_raw, fitted_curve, 4)
                        ws_raw = pushpack_peak(ws_raw, background, 5)
                        ws_raw = pushpack_peak(ws_raw, graphite_peak, 6)
                        ws_raw = pushpack_peak(ws_raw, silicon_peak, 7)
                        ws_res.cell(sam_index, 8).value = fwhm_gn
            else:
                print(f"Failed to fit peaks for sample {sample_name}: 拟合失败，未返回参数")
        except RuntimeError as e:
            print(f"Failed to fit peaks for sample {sample_name}: {e}")

    wb.save('xrd_processed.xlsx')
    print('处理完成，结果已写入')

    