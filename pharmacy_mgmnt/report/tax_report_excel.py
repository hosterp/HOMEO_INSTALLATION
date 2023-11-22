
# excel not working in offline so created PDF for Offline

from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
except ImportError:
    _logger.debug('Can not import xlsxwriter`.')


class TaxReport(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, lines):
        # We can recieve the data entered in the wizard here as data
        worksheet = workbook.add_worksheet("tax_report.xlsx")
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, 1, 20)
        worksheet.set_column(2, 4, 10)
        boldc = workbook.add_format({'bold': True, 'align': 'center'})
        heading_format = workbook.add_format({'bold': True, 'align': 'center', 'size': 12, 'border': 2})
        boldcl = workbook.add_format({'bold': True, 'align': 'center', 'bottom': 2, 'top': 2, 'left': 2})
        boldcl1 = workbook.add_format({'bold': True, 'align': 'left', 'bottom': 2, 'top': 2, 'left': 2})
        boldcc = workbook.add_format({'bold': True, 'align': 'center', 'bottom': 2, 'top': 2})
        boldcr = workbook.add_format({'bold': True, 'align': 'center', 'bottom': 2, 'top': 2, 'right': 2})
        rightr = workbook.add_format({'align': 'right', 'bold': True, 'border': 2})
        rightb = workbook.add_format({'align': 'right', 'bold': True})
        rightbr = workbook.add_format({'align': 'right', 'bold': True, 'bottom': 2, 'top': 2, 'right': 2})
        rightbb = workbook.add_format({'align': 'right', 'bold': True, 'bottom': 2, 'top': 2})

        holiday_regular = workbook.add_format(
            {'align': 'center', 'bold': False, 'text_wrap': True, 'bg_color': '#FFC7CE', })
        regular = workbook.add_format({'align': 'center', 'bold': False})
        attend_regular = workbook.add_format(
            {'align': 'center', 'bold': False, 'font_color': 'brown', 'text_wrap': True})
        centerb = workbook.add_format({'align': 'center', 'bold': True})
        center = workbook.add_format({'align': 'center'})
        italic = workbook.add_format({'italic': True})
        right = workbook.add_format({'align': 'right'})
        bolde = workbook.add_format({'bold': True, 'font_color': 'brown'})
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#D3D3D3',
            'font_color': '#000000',
        })
        format_hidden = workbook.add_format({
            'hidden': True
        })
        align_format = workbook.add_format({
            'align': 'right',
        })


        inv = lines
        worksheet.merge_range('A1:E1', "TRAVANCORE HOMEO MEDICALS, GSTIN :32AYAPS1856Q1ZY", heading_format)
        worksheet.merge_range('A2:B2', "GST BtoB HSN Report by BIll" + datetime.strftime(datetime.strptime(inv[0].from_date, "%Y-%m-%d"), "%d-%m-%Y") + " to " + datetime.strftime(datetime.strptime(inv[0].to_date, "%Y-%m-%d"), "%d-%m-%Y"),boldc)

        # worksheet.merge_range('A2:Q2', month, boldc)
        worksheet.write('A4', 'Customer Name', boldcl)
        worksheet.write('B4', 'GSTIN', boldcc)
        worksheet.write('C4', 'Bill NO', rightbb)
        worksheet.write('D4', 'Bill Date', boldcc)
        worksheet.write('E4', 'Tax Total', rightbr)
        row = 5
        invoice_ids = self.env['account.invoice'].search([('date_invoice', '>=', inv[0].from_date), ('date_invoice', '<=', inv[0].to_date), ('b2b', '=', True), ('packing_slip','=',False),('holding_invoice','=',False)])
        tax_amount_total = 0
        amount_total = 0
        tax_total = 0
        for invoice in invoice_ids:
            worksheet.write('A%s' % row, invoice.partner_id.name or '', boldcl)
            worksheet.write('B%s' % row, invoice.partner_id.gst_no or '', boldcc)
            worksheet.write('C%s' % row, invoice.number2 or '', rightbb)
            worksheet.write('D%s' % row, invoice.date_invoice or '', boldcc)
            worksheet.write('E%s' % row, invoice.amount_tax or '', rightbr)
            row += 1
            worksheet.write('A%s' % row, "HSN", italic)
            worksheet.write('B%s' % row, "QTY", italic)
            worksheet.write('C%s' % row, "TAX", italic)
            worksheet.write('D%s' % row, "TAX AMT", italic)
            worksheet.write('E%s' % row, "TOTAL", italic)
            row += 1
            for line in invoice.invoice_line:
                # same hsn and same tax% line items need to be sum and come in one line
                worksheet.write('A%s' % row, line.hsn_code or '', right)
                worksheet.write('B%s' % row, line.quantity or '', right)
                worksheet.write('C%s' % row, line.invoice_line_tax_id4 or '', right)
                tax_total += line.invoice_line_tax_id4
                worksheet.write('D%s' % row, line.amt_tax or '', right)
                tax_amount_total += line.amt_tax
                worksheet.write('E%s' % row, str(line.amt_w_tax-line.amt_tax) or '', right)
                amount_total += line.amt_w_tax-line.amt_tax
                row += 1

        worksheet.merge_range('A%s:B%s' % (row, row), "Total", boldcl1)
        worksheet.write('C%s' % row, tax_total or '', rightbb)
        worksheet.write('D%s' % row, tax_amount_total or '', boldcc)
        worksheet.write('E%s' % row, amount_total or '', rightbr)


TaxReport('report.pharmacy_mgmnt.report_tax_excel.xlsx', 'tax.report.wizard')