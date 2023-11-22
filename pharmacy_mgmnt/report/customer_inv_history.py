from openerp import models, fields, api, _
from openerp import tools, _
from datetime import datetime, date, timedelta


class CustomerInvoiceHistoryTree(models.TransientModel):
    _name = 'customer.invoice.historytree'

    partner_id = fields.Many2one('res.partner', 'Customer')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    financial_year = fields.Many2one('account.fiscalyear','Financial Year')
    invoices_id = fields.Many2one('account.invoice', 'Invoice No',_rec_name="number2", domain = [('type','=','out_invoice')])
    # bill_no = fields.Char('Bill Number')

    @api.multi
    def action_customer_invoice_his_open_window(self):
        domain = [('packing_slip','=',False),('holding_invoice','=',False),('type','=','out_invoice')]
        if self.invoices_id:
            domain += [('id', '=', self.invoices_id.id)]
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
    @api.multi
    def action_packing_slip_window(self):
        domain = [('packing_invoice', '=', True)]
        if self.invoices_id:
            domain += [('id', '=', self.invoices_id.id)]
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
            res = self.env['account.invoice'].search(domain)
        print(res)
        return{
            'name':_('Packing Slips'),
            'view_type':'tree',
            'view_id': False,
            'view_mode':'tree',
            'res_model':'account.invoice',
            'domain':[('id', 'in', res.ids)],
            'type': 'ir.actions.act_window',
            'target': 'current',


        }
    @api.multi
    def action_holding_invoice_window(self):
        domain = [('holding_invoice','=',True)]
        if self.invoices_id:
            domain += [('id', '=', self.invoices_id.id)]
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
            res = self.env['account.invoice'].search(domain)
        print(res)
        return{
            'name':_('Holding Invoices'),
            'view_type':'tree',
            'view_id': False,
            'view_mode':'tree',
            'res_model':'account.invoice',
            'domain':[('id', 'in', res.ids)],
            'type': 'ir.actions.act_window',
            'target': 'current',


        }





