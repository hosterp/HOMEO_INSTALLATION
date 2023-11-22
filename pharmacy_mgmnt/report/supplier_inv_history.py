from openerp import models, fields, api, _
from openerp import tools, _
from datetime import datetime, date, timedelta


class SupplierInvoiceHistoryTree(models.TransientModel):
    _name = 'supplier.invoice.historytree'

    partner_id = fields.Many2one('res.partner', 'Supplier')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    financial_year = fields.Many2one('account.fiscalyear','Financial Year')
    invoices_id = fields.Many2one('account.invoice', 'Invoice No', domain = [('type','=','in_invoice')])
    bill_no = fields.Char('Bill Number')

    @api.multi
    def action_supplier_invoice_his_open_window(self):
        domain = [('type','=','in_invoice')]
        if self.invoices_id:
            domain += [('id', '=', self.invoices_id.id)]
            res = self.env['account.invoice'].search(domain)
        elif self.bill_no:
            domain +=[('inv_sup_no', '=', self.bill_no)]
            res = self.env['account.invoice'].search(domain)
        else:
            if self.partner_id:
                domain +=[('partner_id', '=', self.partner_id.id)]
            if self.financial_year:
                domain +=[('financial_year', '=', self.financial_year.id)]
            if self.date_from:
                domain +=[('date_invoice', '>=', self.date_from)]
            if self.date_to:
                domain +=[('date_invoice', '<=', self.date_to)]
            if self.bill_no:
                domain +=[('inv_sup_no', '<=', self.bill_no)]
            res = self.env['account.invoice'].search(domain)
        print(res)
        return{
            'name':_('Invoices'),
            'view_type':'tree',
            'view_id': False,
            'view_mode':'tree',
            'res_model':'account.invoice',
            'domain':[('id', 'in', res.ids)],
            'type': 'ir.actions.act_window',
            'target': 'current',


        }





