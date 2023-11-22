from openerp import models, fields, api, _
from openerp import tools, _
from datetime import datetime, date, timedelta


class CustomerInvoiceReport(models.TransientModel):
    _name = 'customer.invoice.report'

    partner_id = fields.Many2one('res.partner', 'Customer')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    product = fields.Many2one('product.product', 'Product')
    potency = fields.Many2one('product.medicine.subcat', 'Potency')
    packing = fields.Many2one('product.medicine.packing', 'Packing')
    company = fields.Many2one('product.medicine.responsible', 'Company')
    group = fields.Many2one('tax.combo.new', 'Group')

    @api.multi
    def action_customer_invoice_open_window(self):
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }
        data = self.env['ir.actions.report.xml'].search(
            [('model', '=', 'customer.invoice.report'),
             ('report_name', '=', 'pharmacy_mgmnt.report_customer_invoice_template_new',)])
        data.download_filename = 'Customer invoice report.pdf'
        return {
            'name': 'Customer Invoice Report',
            'type': 'ir.actions.report.xml',
            'report_name': 'pharmacy_mgmnt.report_customer_invoice_template_new',
            'datas': datas,
            'report_type': 'qweb-pdf'
        }

    @api.multi
    def get_details(self):
        lst = []
        domain = [('invoice_id.state', '=', 'paid'), ('invoice_id.type', '=', 'out_invoice')]
        if self.partner_id:
            domain += [('invoice_id.partner_id', '=', self.partner_id.id)]
        if self.product:
            domain += [('product_id', '=', self.product.id)]
        if self.date_from:
            domain += [('invoice_id.date_invoice', '>=', self.date_from)]
        if self.date_to:
            domain += [('invoice_id.date_invoice', '<=', self.date_to)]
        if self.potency:
            domain += [('medicine_name_subcat', '<=', self.potency.id)]
        if self.group:
            domain += [('medicine_grp', '<=', self.group.id)]
        if self.company:
            domain += [('product_of', '<=', self.company.id)]
        if self.packing:
            domain += [('medicine_name_packing', '<=', self.packing.id)]
        invoices = self.env['account.invoice.line'].search(domain)

        for rec in invoices:
            vals = {
                'date': rec.invoice_id.date_invoice,
                'medicine': rec.product_id.name,
                'exp': rec.expiry_date,
                'mfd': rec.manf_date,
                'amount': round(rec.amt_w_tax, 2),
                'total_amt': 0,
                # 'group': rec.medicine_grp.medicine_grp.med_grp,
                'group': rec.medicine_grp.med_grp,
                'potency': rec.medicine_name_subcat.medicine_rack_subcat,
                'packing': rec.medicine_name_packing.medicine_pack,
                'customer': rec.invoice_id.partner_id.name,
                'company': rec.product_of.name_responsible
            }
            lst.append(vals)
        sum = 0
        for vals in lst:
            sum = round(sum + vals['amount'], 2)
        for vals in lst:
            vals['total_amt'] = sum
        return lst

        sum = 0
        for vals in lst:
            sum = round(sum + vals['amount'], 2)
        for vals in lst:
            vals['total_amt'] = sum
        return lst
