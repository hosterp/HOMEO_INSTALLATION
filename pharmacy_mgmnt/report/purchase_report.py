from openerp import models, fields, api, _
from openerp import tools, _
from datetime import datetime, date, timedelta


class CustomerInvoiceReport(models.TransientModel):
    _name = 'purchase.invoice.report'

    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    product = fields.Many2one('product.product', 'Product')
    group = fields.Many2one('tax.combo.new', 'Group')
    potency = fields.Many2one('product.medicine.subcat', 'Potency')
    packing = fields.Many2one('product.medicine.packing', 'Packing')
    company = fields.Many2one('product.medicine.responsible', 'Company')

    @api.multi
    def action_purchase_report_open_window(self):
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }
        # data = self.env['ir.actions.report.xml'].search(
        #     [('model', '=', 'purchase.invoice.report'),
        #      ('report_name', '=', 'pharmacy_mgmnt.purchase_report_template_new',)])
        # data.download_filename = 'purchase report.pdf'
        return {
            'name': 'Purchase Report',
            'type': 'ir.actions.report.xml',
            'report_name': 'pharmacy_mgmnt.purchase_report_template_new',
            'datas': datas,
            'report_type': 'qweb-pdf'
        }

    @api.multi
    def view_purchase_report(self):
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'pharmacy_mgmnt.purchase_report_template_new',
            'datas': datas,
            'report_type': 'qweb-html',
        }

    @api.multi
    def get_details(self):
        invoice_lines = False
        if self.date_from:
            domain = [('invoice_id.date_invoice', '>=', self.date_from),
                 ('invoice_id.date_invoice', '<=', self.date_to),
                 ('invoice_id.type','!=','out_invoice')]
            if self.product:
                domain += [('product_id', '>=', self.product.id)]
            if self.company:
                domain += [('product_of', '>=', self.company.id)]
            if self.group:
                domain += [('medicine_grp', '>=', self.group.id)]
            if self.packing:
                domain += [('medicine_name_packing', '>=', self.packing.id)]
            if self.potency:
                domain += [('medicine_name_subcat', '>=', self.potency.id)]

            invoice_lines = self.env['account.invoice.line'].search(domain)

        return invoice_lines
