from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import models, fields, api, tools

from openerp.exceptions import Warning
from openerp.tools.translate import _


class CreditLimitCustomer(models.Model):
    _inherit = 'res.partner'

    def _compute_credited_amt(self):
        for rec in self:
            customer_invoices = rec.env['account.invoice'].search([('pay_mode', '=', 'credit'),
                                                                   ('partner_id', '=', rec.id),
                                                                   ('type', '=', 'out_invoice'),
                                                                   ('state', '=', 'open')])
            rec.used_credit_amt = sum(customer_invoices.mapped('amount_total'))
            if rec.days_credit_limit:
                last_payment = self.env['partner.payment'].search([('partner_id', '=', rec.id), ('balance_amount', '=', 0)],
                                                                  order='id desc', limit=1)

                # date_today = fields.Date.today()
                if last_payment.date:
                    pass
                else:
                    date_today = fields.Date.today()
                    x = datetime.strptime(date_today, '%Y-%m-%d')
                    next_date = x + relativedelta(days=rec.days_credit_limit)
                    cal_date = datetime.strftime(next_date, '%Y-%m-%d')
                    rec.write({'credit_end_date': cal_date})

    limit_amt = fields.Float('Credit Limit Amount')
    used_credit_amt = fields.Float('Used Amount', compute="_compute_credited_amt")
    days_credit_limit = fields.Float('Credit Limit Days')
    credit_end_date = fields.Date(string="Credit end Date")
