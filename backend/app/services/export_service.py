"""
Export Service — Generate Excel, PDF, and CSV shortage reports.
"""

import io
import logging
from datetime import datetime, timezone

from app.services.priority_service import get_priority_label, get_priority_color

logger = logging.getLogger(__name__)


def export_to_excel(report_data: dict) -> bytes:
    """Generate an Excel (.xlsx) shortage report."""
    try:
        import xlsxwriter

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet("Shortage Report")

        # Title format
        title_fmt = workbook.add_format({
            "bold": True, "font_size": 16, "font_color": "#1E6FD9",
            "bottom": 2, "bottom_color": "#1E6FD9",
        })

        # Header format
        header_fmt = workbook.add_format({
            "bold": True, "font_size": 11, "bg_color": "#1E6FD9",
            "font_color": "#FFFFFF", "border": 1, "text_wrap": True,
            "valign": "vcenter", "align": "center",
        })

        # Priority colors
        critical_fmt = workbook.add_format({"bg_color": "#FEE2E2", "font_color": "#DC2626", "border": 1, "align": "center"})
        high_fmt = workbook.add_format({"bg_color": "#FFF7ED", "font_color": "#EA580C", "border": 1, "align": "center"})
        medium_fmt = workbook.add_format({"bg_color": "#FEFCE8", "font_color": "#CA8A04", "border": 1, "align": "center"})
        safe_fmt = workbook.add_format({"bg_color": "#F0FDF4", "font_color": "#16A34A", "border": 1, "align": "center"})

        cell_fmt = workbook.add_format({"border": 1, "valign": "vcenter"})
        number_fmt = workbook.add_format({"border": 1, "align": "center", "valign": "vcenter"})
        date_fmt = workbook.add_format({"font_size": 10, "font_color": "#6B7280"})

        # Title
        worksheet.merge_range("A1:H1", report_data.get("title", "Shortage Report"), title_fmt)
        worksheet.write("A2", f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", date_fmt)
        worksheet.write("A3", f"Total Required: {report_data.get('total_required', 0)} | "
                        f"Critical: {report_data.get('critical_count', 0)} | "
                        f"Below Minimum: {report_data.get('below_minimum_count', 0)}", date_fmt)

        # Headers
        headers = ["#", "Medicine Name", "Arabic Name", "Current Stock",
                   "Minimum Stock", "Required Qty", "Priority", "Notes"]
        for col, header in enumerate(headers):
            worksheet.write(4, col, header, header_fmt)

        # Column widths
        widths = [5, 35, 25, 14, 14, 14, 12, 25]
        for col, width in enumerate(widths):
            worksheet.set_column(col, col, width)

        # Data rows
        medicines = report_data.get("medicines", [])
        for row_idx, med in enumerate(medicines):
            row = row_idx + 5
            priority = med.get("priority", "safe")

            # Priority format selection
            if priority == "critical":
                p_fmt = critical_fmt
            elif priority == "high":
                p_fmt = high_fmt
            elif priority == "medium":
                p_fmt = medium_fmt
            else:
                p_fmt = safe_fmt

            worksheet.write_number(row, 0, row_idx + 1, number_fmt)
            worksheet.write_string(row, 1, med.get("name", ""), cell_fmt)
            worksheet.write_string(row, 2, med.get("name_arabic", "") or "", cell_fmt)
            worksheet.write_number(row, 3, med.get("current_stock", 0), number_fmt)
            worksheet.write_number(row, 4, med.get("minimum_stock", 10), number_fmt)
            worksheet.write_number(row, 5, med.get("required_quantity", 0), number_fmt)
            worksheet.write_string(row, 6, get_priority_label(priority) if isinstance(priority, str) else priority, p_fmt)
            worksheet.write_string(row, 7, med.get("notes", "") or "", cell_fmt)

        workbook.close()
        output.seek(0)
        return output.getvalue()

    except Exception as e:
        logger.error(f"Excel export failed: {e}")
        raise


def export_to_csv(report_data: dict) -> bytes:
    """Generate a CSV shortage report."""
    import csv

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "#", "Medicine Name", "Arabic Name", "Current Stock",
        "Minimum Stock", "Required Qty", "Priority", "Notes"
    ])

    # Data
    medicines = report_data.get("medicines", [])
    for idx, med in enumerate(medicines):
        writer.writerow([
            idx + 1,
            med.get("name", ""),
            med.get("name_arabic", "") or "",
            med.get("current_stock", 0),
            med.get("minimum_stock", 10),
            med.get("required_quantity", 0),
            med.get("priority", "safe"),
            med.get("notes", "") or "",
        ])

    return output.getvalue().encode("utf-8-sig")  # BOM for Excel compatibility


def export_to_pdf(report_data: dict) -> bytes:
    """Generate a PDF shortage report using ReportLab."""
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        output = io.BytesIO()
        doc = SimpleDocTemplate(
            output, pagesize=landscape(A4),
            rightMargin=15 * mm, leftMargin=15 * mm,
            topMargin=15 * mm, bottomMargin=15 * mm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle", parent=styles["Title"],
            fontSize=18, textColor=colors.HexColor("#1E6FD9"),
            spaceAfter=5 * mm,
        )
        subtitle_style = ParagraphStyle(
            "Subtitle", parent=styles["Normal"],
            fontSize=10, textColor=colors.HexColor("#6B7280"),
            spaceAfter=8 * mm,
        )

        elements = []

        # Title
        elements.append(Paragraph(report_data.get("title", "Shortage Report"), title_style))
        elements.append(Paragraph(
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | "
            f"Total Required: {report_data.get('total_required', 0)} | "
            f"Critical: {report_data.get('critical_count', 0)}",
            subtitle_style
        ))

        # Table data
        table_data = [["#", "Medicine Name", "Current\nStock", "Min\nStock",
                       "Required\nQty", "Priority", "Notes"]]

        medicines = report_data.get("medicines", [])
        for idx, med in enumerate(medicines):
            priority = med.get("priority", "safe")
            table_data.append([
                str(idx + 1),
                med.get("name", ""),
                str(med.get("current_stock", 0)),
                str(med.get("minimum_stock", 10)),
                str(med.get("required_quantity", 0)),
                get_priority_label(priority) if isinstance(priority, str) else str(priority),
                med.get("notes", "") or "",
            ])

        # Build table
        col_widths = [25, 180, 60, 50, 60, 60, 120]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)

        # Table styling
        style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E6FD9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (1, 1), (1, -1), "LEFT"),
            ("ALIGN", (-1, 1), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]

        # Priority row coloring
        for idx, med in enumerate(medicines):
            row = idx + 1
            priority = med.get("priority", "safe")
            if priority == "critical":
                style_commands.append(("TEXTCOLOR", (5, row), (5, row), colors.HexColor("#DC2626")))
            elif priority == "high":
                style_commands.append(("TEXTCOLOR", (5, row), (5, row), colors.HexColor("#EA580C")))
            elif priority == "medium":
                style_commands.append(("TEXTCOLOR", (5, row), (5, row), colors.HexColor("#CA8A04")))

        table.setStyle(TableStyle(style_commands))
        elements.append(table)

        doc.build(elements)
        output.seek(0)
        return output.getvalue()

    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        raise
