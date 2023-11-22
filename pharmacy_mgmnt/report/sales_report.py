from openerp import models, fields, api, _
from openerp import tools, _
from datetime import datetime, date, timedelta


class InvoiceDetails(models.Model):
    _name = 'sales.details'
    _inherits = {'account.invoice': 'invoice_id'}

    invoice_id = fields.Many2one('account.invoice', required=True)
    sales_details_id = fields.Many2one('sales.report')
    test = fields.Integer()

    @api.multi
    def open_invoice(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        redirect_url = "%s/web#id=%d&view_type=form&model=account.invoice&menu_id=331&action=400" % (
            base_url, self.invoice_id.id)
        print('redirect_url', redirect_url)
        print('self.invoice_ids.invoice_id.id', self.invoice_id.id)
        return {
            'type': 'ir.actions.act_url',
            'url': redirect_url,
            'target': 'self',
        }


class SalesReport(models.Model):
    _name = 'sales.report'
    _order = 'date desc'

    name = fields.Char()
    date = fields.Date(default=fields.Date.today)
    partner_id = fields.Many2one('res.partner', 'Customer')
    res_person_id = fields.Many2one('res.partner', 'Responsible Person')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    product = fields.Many2one('product.product', 'Product')
    potency = fields.Many2one('product.medicine.subcat', 'Potency')
    packing = fields.Many2one('product.medicine.packing', 'Packing')
    company = fields.Many2one('product.medicine.responsible', 'Company')
    group = fields.Many2one('tax.combo.new', 'Group')
    state = fields.Selection([('open', 'Open'), ('draft', 'Draft'), ('paid', 'Paid')])
    invoice_ids = fields.One2many('sales.details', 'sales_details_id', readonly=False,
                                  store=True)
    pay_mode = fields.Selection([('cash', 'Cash'), ('credit', 'Credit'),('upi', 'UPI'),], 'Payment Mode',)

    @api.model
    def create(self, vals):
        print('hello')
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('sales.report.sequence')
            result = super(SalesReport,self).create(vals)
            print('hello1',result.name)
            return result
        else:
            pass

    @api.multi
    def print_sale_report(self):
        assert len(self) == 1
        self.sent = True
        data = self.env['ir.actions.report.xml'].search(
            [('model', '=', 'sales.report'),
             ('report_name', '=', 'pharmacy_mgmnt.sales_report_id',)])
        data.download_filename = 'Sales report.pdf'
        return self.env['report'].get_action(self, 'pharmacy_mgmnt.sales_report_id')
    @api.multi
    @api.model
    def get_all_sales(self):
        domain = [('type', '=', 'out_invoice')]
        if self.date_from:
            domain = [('date_invoice', '>=', self.date_from)]
        if self.date_to:
            domain += [('date_invoice', '<=', self.date_to)]
        if self.partner_id:
            domain += [('partner_id', '=', self.partner_id.id)]
        if self.res_person_id:
            domain += [('res_person', '=', self.res_person_id.id)]
        if self.product:
            domain += [('invoice_line.product_id', '=', self.product.id)]
        if self.potency:
            domain += [('invoice_line.medicine_name_subcat', '=', self.potency.id)]
        if self.packing:
            domain += [('invoice_line.medicine_name_packing', '=', self.packing.id)]
        if self.company:
            domain += [('invoice_line.product_of', '=', self.company.id)]
        if self.group:
            domain += [('invoice_line.medicine_grp', '=', self.group.id)]
        if self.state:
            domain += [('state', '=', self.state)]
        if self.pay_mode:
            domain += [('pay_mode', '=', self.pay_mode)]
        for rec in self:
            if rec.invoice_ids:
               rec.invoice_ids = [(5, 0, 0)]
            rec.account_id = 25
            rec.invoice_ids = []
            list = []
            invoices = self.env['account.invoice'].search(domain)
            if invoices:
                for line in invoices:
                    list.append([0, 0, {'partner_id': line.partner_id.id,
                                        'name': line.name,
                                        'test': line.id,
                                        'reference': line.reference,
                                        'type': line.type,
                                        'state': line.state,
                                        'amount_total': line.amount_total,
                                        'amount_untaxed': line.amount_untaxed,
                                        'residual': line.residual,
                                        'de_residual': line.residual,
                                        'currency_id': line.currency_id.id,
                                        'origin': line.origin,
                                        'date_invoice': line.date_invoice,
                                        'journal_id': line.journal_id.id,
                                        'period_id': line.period_id.id,
                                        'company_id': line.company_id.id,
                                        # 'user_id': line.user_id.id,
                                        'date_due': line.date_due,
                                        'number2': line.number2,
                                        'account_id': line.account_id.id,
                                        'invoice_id': line.id,
                                        'pay_mode':line.pay_mode,
                                        }
                                 ])
            rec.invoice_ids = list
            domain = []

    # @api.onchange('partner_id')
    # def onchange_partner_id(self):
    #     if self.partner_id and self.res_person_id:
    #         for rec in self:
    #             rec.account_id = 25
    #             rec.invoice_ids = []
    #             list = []
    #             invoices = self.env['account.invoice'].search(
    #                 [('partner_id', '=', rec.partner_id.id), ('res_person', '=', rec.res_person_id.id),
    #                  ])
    #             if invoices:
    #                 for line in invoices:
    #                     if line.state == 'open':
    #                         list.append([0, 0, {'partner_id': line.partner_id.id,
    #                                             'name': line.name,
    #                                             'reference': line.reference,
    #                                             'type': line.type,
    #                                             'state': line.state,
    #                                             'amount_total': line.amount_total,
    #                                             'amount_untaxed': line.amount_untaxed,
    #                                             'residual': line.residual,
    #                                             'de_residual': line.residual,
    #                                             'currency_id': line.currency_id.id,
    #                                             'origin': line.origin,
    #                                             'date_invoice': line.date_invoice,
    #                                             'journal_id': line.journal_id.id,
    #                                             'period_id': line.period_id.id,
    #                                             'company_id': line.company_id.id,
    #                                             # 'user_id': line.user_id.id,
    #                                             'date_due': line.date_due,
    #                                             'number2': line.number2,
    #                                             'account_id': line.account_id.id,
    #                                             'invoice_id': line.id
    #                                             }
    #                                      ])
    #             rec.invoice_ids = list
    #
    #     else:
    #         if self.partner_id:
    #             for rec in self:
    #                 rec.account_id = 25
    #                 rec.invoice_ids = []
    #                 list = []
    #                 invoices = self.env['account.invoice'].search(
    #                     [('partner_id', '=', rec.partner_id.id),
    #                      ])
    #                 if invoices:
    #                     for line in invoices:
    #                         if line.state == 'open':
    #                             list.append([0, 0, {'partner_id': line.partner_id.id,
    #                                                 'name': line.name,
    #                                                 'reference': line.reference,
    #                                                 'type': line.type,
    #                                                 'state': line.state,
    #                                                 'amount_total': line.amount_total,
    #                                                 'amount_untaxed': line.amount_untaxed,
    #                                                 'residual': line.residual,
    #                                                 'de_residual': line.residual,
    #                                                 'currency_id': line.currency_id.id,
    #                                                 'origin': line.origin,
    #                                                 'date_invoice': line.date_invoice,
    #                                                 'journal_id': line.journal_id.id,
    #                                                 'period_id': line.period_id.id,
    #                                                 'company_id': line.company_id.id,
    #                                                 # 'user_id': line.user_id.id,
    #                                                 'date_due': line.date_due,
    #                                                 'number2': line.number2,
    #                                                 'account_id': line.account_id.id,
    #                                                 'invoice_id': line.id
    #                                                 }
    #                                          ])
    #                 rec.invoice_ids = list
    #         else:
    #             pass
    #
    # @api.onchange('res_person_id')
    # def onchange_res_partner_id(self):
    #     if self.partner_id and self.res_person_id:
    #         for rec in self:
    #             rec.account_id = 25
    #             rec.invoice_ids = []
    #             list = []
    #             invoices = self.env['account.invoice'].search(
    #                 [('partner_id', '=', rec.partner_id.id), ('res_person', '=', rec.res_person_id.id),
    #                  ])
    #             if invoices:
    #                 for line in invoices:
    #                     if line.state == 'open':
    #                         list.append([0, 0, {'partner_id': line.partner_id.id,
    #                                             'name': line.name,
    #                                             'reference': line.reference,
    #                                             'type': line.type,
    #                                             'state': line.state,
    #                                             'amount_total': line.amount_total,
    #                                             'amount_untaxed': line.amount_untaxed,
    #                                             'residual': line.residual,
    #                                             'de_residual': line.residual,
    #                                             'currency_id': line.currency_id.id,
    #                                             'origin': line.origin,
    #                                             'date_invoice': line.date_invoice,
    #                                             'journal_id': line.journal_id.id,
    #                                             'period_id': line.period_id.id,
    #                                             'company_id': line.company_id.id,
    #                                             # 'user_id': line.user_id.id,
    #                                             'date_due': line.date_due,
    #                                             'number2': line.number2,
    #                                             'account_id': line.account_id.id,
    #                                             'invoice_id': line.id
    #                                             }
    #                                      ])
    #             rec.invoice_ids = list
    #     else:
    #         if self.res_person_id:
    #             for rec in self:
    #                 rec.account_id = 25
    #                 rec.invoice_ids = []
    #                 list = []
    #                 invoices = self.env['account.invoice'].search(
    #                     [('res_person', '=', rec.res_person_id.id),
    #                      ])
    #                 if invoices:
    #                     for line in invoices:
    #                         if line.state == 'open':
    #                             list.append([0, 0, {'partner_id': line.partner_id.id,
    #                                                 'name': line.name,
    #                                                 'reference': line.reference,
    #                                                 'type': line.type,
    #                                                 'state': line.state,
    #                                                 'amount_total': line.amount_total,
    #                                                 'amount_untaxed': line.amount_untaxed,
    #                                                 'residual': line.residual,
    #                                                 'de_residual': line.residual,
    #                                                 'currency_id': line.currency_id.id,
    #                                                 'origin': line.origin,
    #                                                 'date_invoice': line.date_invoice,
    #                                                 'journal_id': line.journal_id.id,
    #                                                 'period_id': line.period_id.id,
    #                                                 'company_id': line.company_id.id,
    #                                                 # 'user_id': line.user_id.id,
    #                                                 'date_due': line.date_due,
    #                                                 'number2': line.number2,
    #                                                 'account_id': line.account_id.id,
    #                                                 'invoice_id': line.id
    #                                                 }
    #                                          ])
    #                 rec.invoice_ids = list
    #         else:
    #             pass

    # @api.multi
    # def action_customer_invoice_open_window(self):
    #     datas = {
    #         'ids': self._ids,
    #         'model': self._name,
    #         'form': self.read(),
    #         'context': self._context,
    #     }
    #
    #     return {
    #         'name': 'Customer Invoice Report',
    #         'type': 'ir.actions.report.xml',
    #         'report_name': 'pharmacy_mgmnt.report_customer_invoice_template_new',
    #         'datas': datas,
    #         'report_type': 'qweb-pdf'
    #     }

    # @api.multi
    # def get_details(self):
    #     lst = []
    #     domain = [('invoice_id.state', '=', 'paid'), ('invoice_id.type', '=', 'out_invoice')]
    #     if self.partner_id:
    #         domain += [('invoice_id.partner_id', '=', self.partner_id.id)]
    #     if self.product:
    #         domain += [('product_id', '=', self.product.id)]
    #     if self.date_from:
    #         domain += [('invoice_id.date_invoice', '>=', self.date_from)]
    #     if self.date_to:
    #         domain += [('invoice_id.date_invoice', '<=', self.date_to)]
    #     if self.potency:
    #         domain += [('medicine_name_subcat', '<=', self.potency.id)]
    #     if self.group:
    #         domain += [('medicine_grp', '<=', self.group.id)]
    #     if self.company:
    #         domain += [('product_of', '<=', self.company.id)]
    #     if self.packing:
    #         domain += [('medicine_name_packing', '<=', self.packing.id)]
    #     invoices = self.env['account.invoice.line'].search(domain)
    #
    #     for rec in invoices:
    #         vals = {
    #             'date': rec.invoice_id.date_invoice,
    #             'medicine': rec.product_id.name,
    #             'exp': rec.expiry_date,
    #             'mfd': rec.manf_date,
    #             'amount': round(rec.amt_w_tax, 2),
    #             'total_amt': 0,
    #             # 'group': rec.medicine_grp.medicine_grp.med_grp,
    #             'group': rec.medicine_grp.med_grp,
    #             'potency': rec.medicine_name_subcat.medicine_rack_subcat,
    #             'packing': rec.medicine_name_packing.medicine_pack,
    #             'customer': rec.invoice_id.partner_id.name,
    #             'company': rec.product_of.name_responsible
    #         }
    #         lst.append(vals)
    #     sum = 0
    #     for vals in lst:
    #         sum = round(sum + vals['amount'], 2)
    #     for vals in lst:
    #         vals['total_amt'] = sum
    #     return lst
    #
    #     sum = 0
    #     for vals in lst:
    #         sum = round(sum + vals['amount'], 2)
    #     for vals in lst:
    #         vals['total_amt'] = sum
    #     return lst
