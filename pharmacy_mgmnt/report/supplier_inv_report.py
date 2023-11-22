from openerp import models, fields, api, _
from datetime import datetime, date, timedelta



class SupplierInvoiceReport(models.TransientModel):
    _name = 'supplier.invoice.report'

    partner_id = fields.Many2one('res.partner', 'Supplier')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')

    @api.multi
    def action_supplier_invoice_open_window(self):
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }
        data = self.env['ir.actions.report.xml'].search(
            [('model', '=', 'supplier.invoice.report'),
             ('report_name', '=', 'pharmacy_mgmnt.report_supplier_invoice_template_new',)])
        data.download_filename = 'Supplier invoice report.pdf'
        return {
            'name': 'Supplier Invoice Report',
            'type': 'ir.actions.report.xml',
            'report_name': 'pharmacy_mgmnt.report_supplier_invoice_template_new',
            'datas': datas,
            'report_type': 'qweb-pdf'
        }

    @api.multi
    def get_details(self):
        d1 = self.date_from
        d2 = self.date_to
        d1 = datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.strptime(d2, "%Y-%m-%d")
        lst = []
        if self.partner_id:
            cust_invs = self.env['account.invoice'].search(
                [('date_invoice', '>=', self.date_from), ('date_invoice', '<=', self.date_to),
                 ('partner_id', '=', self.partner_id.id)])
            for rec in cust_invs:

                for lines in rec.invoice_line:
                    vals = {

                        'date':rec.date_invoice,
                        'medicine':lines.product_id.name,
                        'exp':lines.expiry_date,
                        'mfd':lines.manf_date,
                        'amount':round(lines.amount_w_tax,2),
                        'total_amt':0

                    }
                    lst.append(vals)
            sum=0
            for vals in lst:
                sum = round(sum + vals['amount'],2)
            for vals in lst:
                vals['total_amt'] = sum
            return lst




