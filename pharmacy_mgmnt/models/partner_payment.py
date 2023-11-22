from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from openerp.osv import osv
from openerp.tools import safe_eval
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta


class InvoiceDetails(models.Model):
    _name = 'invoice.details'
    _inherits = {'account.invoice': 'invoice_id'}

    invoice_id = fields.Many2one('account.invoice', required=True)
    partner_payment_id = fields.Many2one('partner.payment')
    select = fields.Boolean()
    de_residual = fields.Float()
    calc = fields.Float()

    # def onchange_de_residual(self):
    #     print('shooo')

    # @api.multi
    # @api.onchange("select")
    # def onchange_select(self):
    #     payment_amt = 0
    #     if  self.partner_payment_id.payment_amount:
    #         if self.partner_payment_id.calc_amount:
    #             payment_amt = self.partner_payment_id.calc_amount
    #         else:
    #             payment_amt = self.partner_payment_id.payment_amount
    #         for records in self._origin:
    #             residual = records.residual
    #             if residual < payment_amt:
    #                 ref = self.partner_payment_id.reference_number
    #                 data = self.env['partner.payment'].search([('reference_number', '=', ref)])
    #                 new_amount = data.payment_amount - records.residual
    #                 self._origin.write({
    #                     'residual': 0,
    #                     'state': 'paid',
    #                 })
    #                 data.write({
    #                     'calc_amount': new_amount,
    #                 })
    #                 self.env.cr.commit()
    #                 # self.env.cr.commit(data)
    #                 return
    #             else:
    #                 pass
    #             if residual > payment_amt:
    #                 raise osv.except_osv(_('Warning!'), _("Press PAY button to complete the payment"))
    #
    #             # ref = self.partner_payment_id.reference_number
    #                 # residual = residual - payment_amt
    #                 # data = self.env['partner.payment'].search([('reference_number', '=', ref)])
    #                 # data.write({
    #                 #     'calc_amount': 0,
    #                 # })
    #                 # self.env.cr.commit()
    #                 # self._origin.write({
    #                 #     'residual': 0,
    #                 #     'state': 'open',
    #                 # })
    #
    #             else:
    #                 pass
    #             if residual == payment_amt:
    #                 ref = self.partner_payment_id.reference_number
    #                 payment_amt = payment_amt - residual
    #                 data = self.env['partner.payment'].search([('reference_number', '=', ref)])
    #                 data.write({
    #                     'calc_amount': 0,
    #                     # 'account_id': 25,
    #                 })
    #                 self.env.cr.commit()
    #                 self._origin.write({
    #                         'residual': 0,
    #                         'state': 'paid',
    #                     })
    #             else:
    #                 pass


class PartnerPayment(models.Model):
    _inherits = {'account.voucher': 'voucher_relation_id'}
    _name = 'partner.payment'
    _rec_name = 'reference_number'
    _order = 'reference_number desc'

    voucher_relation_id = fields.Many2one('account.voucher', required=True)
    res_person_id = fields.Many2one('res.partner', domain=[('res_person_id', '=', True)])
    partner_id = fields.Many2one('res.partner', domain=[('customer', '=', True), ('res_person_id', '=', False)])
    reference_number = fields.Integer()
    date = fields.Date(default=fields.Date.today)
    payment_method = fields.Selection([('cheque', 'Cheque'), ('cash', 'Cash'), ('UPI', 'UPI')],
                                      string="Mode of Payment", default='cash')
    cheque_no = fields.Char()
    cheque_date = fields.Date(default=date.today())
    deposit_date = fields.Date()
    clearence_date = fields.Date()
    remarks = fields.Text()
    bank = fields.Char('Bank')
    branch = fields.Char('Branch')
    ifsc = fields.Char('IFSC')
    # total_amount = fields.Float(compute='_compute_amount')
    total_amount = fields.Float(compute='_compute_value', store=True)
    payment_amount = fields.Float()
    pays = fields.Float(default=0)
    balance_amount = fields.Float(compute='_compute_balance')
    calc_amount = fields.Float()
    invoice_ids = fields.One2many('invoice.details', 'partner_payment_id', readonly=False,
                                  store=True)
    # invoice_ids = fields.One2many('invoice.details', 'partner_payment_id', compute='generate_lines', readonly=False,
    #                               store=True)
    state = fields.Selection([('new', 'New'), ('draft', 'Draft'), ('bounced', 'Bounced'), ('paid', 'Paid')])
    advance_amount = fields.Float('Advance Amount', related="partner_id.advance_amount")
    payment_total_calculation = fields.Float()
    click = fields.Boolean(string='clicked')
    cheque_balance = fields.Float('Check Balance')
    # chekbox=fields.Selection([('yes','Yes'),('no','No')],default='no')

    @api.constrains('deposit_date', 'clearence_date')
    def _check_deposit_and_const(self):
        for record in self:
            if record.deposit_date and record.deposit_date < record.cheque_date:
                raise ValidationError("The deposit date cannot be earlier than the cheque date.")
            if record.clearence_date and record.clearence_date < record.deposit_date:
                raise ValidationError("The clearence date cannot be earlier than the deposit date.")

    @api.onchange('payment_amount')
    def onchange_payment_amount(self):
        if self.payment_amount != 0:
            if self.advance_amount and self.payment_method != 'cheque':
                self.payment_amount+=self.advance_amount
        self.calc_amount = self.payment_amount

    @api.onchange('deposit_date', 'clearence_date')
    def _check_deposit_and_clearence_dates(self):
        for record in self:
            if record.deposit_date and record.deposit_date < record.cheque_date:
                raise ValidationError("The deposit date cannot be earlier than the cheque date.")
            if record.clearence_date and record.clearence_date < record.deposit_date:
                raise ValidationError("The clearence date cannot be earlier than the deposit date.")



    # @api.onchange('chekbox')
    # def _advance_amount_calc(self):
    #     for rec in self:
    #         advance=self.advance_amount
    #         if rec.chekbox == 'yes':
    #             rec.payment_amount+=rec.advance_amount
    #         else:
    #            rec.payment_amount-=rec.advance_amount


    # @api.onchange('balance_amount')
    # def onchange_payment_amount(self):
    #     # self.pays += 1
    #     for record in self:
    #         if record.invoice_ids:
    #             total = sum(line.residual for line in record.invoice_ids)
    #             balance = sum(line.amount_total for line in record.invoice_ids)
    #             calc_value = record.payment_amount - (balance - total)
    #             print(total, 'totaltotal')
    #             print(balance, 'balancebalance')
    #             if calc_value <= 0:
    #                 self.calc_amount = self.payment_amount
    #             else:
    #                 self.calc_amount = calc_value
    #             print(calc_value, 'calc_valuecalc_valuecalc_value')
    #             print(self.pays,'payspausysy')
    # modified code
    #

    @api.multi
    def cheque_bounce_button(self):
        if self.cheque_bounce_button:
            if self.state == 'paid':
                self.state = 'bounced'
                self.click = True
                # status_update=self.env['cheque.entry'].search([('invoice_ids', '=',self.invoice_ids.invoice_id.id),('state','=','draft'),('deposit_date','=',self.deposit_date)])
                status_update= self.env['cheque.entry'].search([('cheque_no', '=' , self.cheque_no)])
                for record in status_update:
                    record.state = 'bounce'
                for rec in self.invoice_ids:
                    rec.state ='open'

    @api.multi
    def cheque_paid_button(self):
        self.advance_amount += self.cheque_balance
        self.cheque_balance = 0
        self.click = True
        # if self.cheque_bounce_button:
        if self.state == 'paid':
            status_update = self.env['cheque.entry'].search([('cheque_no', '=', self.cheque_no)])
            for record in status_update:
                record.state = 'paid'
            for rec in self.invoice_ids:
                rec.state = 'paid'
                    # print(status_update,'status_update_paidstatus_update_paid')
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id and self.res_person_id:
            for rec in self:
                rec.account_id = 25
                rec.invoice_ids = []
                list = []
                invoices = self.env['account.invoice'].search(
                    [('partner_id', '=', rec.partner_id.id), ('res_person', '=', rec.res_person_id.id),('pay_mode', '=','credit')
                     ])
                if invoices:
                    for line in invoices:
                        if line.state == 'open':
                            list.append([0, 0, {'partner_id': line.partner_id.id,
                                                'name': line.name,
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
                                                'invoice_id': line.id
                                                }
                                         ])
                rec.invoice_ids = list

        else:
            if self.partner_id:
                for rec in self:
                    rec.account_id = 25
                    rec.invoice_ids = []
                    list = []
                    invoices = self.env['account.invoice'].search(
                        [('partner_id', '=', rec.partner_id.id),('pay_mode', '=','credit')
                         ])
                    if invoices:
                        for line in invoices:
                            if line.state == 'open':
                                list.append([0, 0, {'partner_id': line.partner_id.id,
                                                    'name': line.name,
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
                                                    'invoice_id': line.id
                                                    }
                                             ])
                    rec.invoice_ids = list
            else:
                pass

    @api.onchange('res_person_id')
    def onchange_res_partner_id(self):
        if self.partner_id and self.res_person_id:
            for rec in self:
                rec.account_id = 25
                rec.invoice_ids = []
                list = []
                invoices = self.env['account.invoice'].search(
                    [('partner_id', '=', rec.partner_id.id), ('res_person', '=', rec.res_person_id.id),('pay_mode', '=','credit')
                     ])
                if invoices:
                    for line in invoices:
                        if line.state == 'open':
                            list.append([0, 0, {'partner_id': line.partner_id.id,
                                                'name': line.name,
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
                                                'invoice_id': line.id
                                                }
                                         ])
                rec.invoice_ids = list
        else:
            if self.res_person_id:
                for rec in self:
                    rec.account_id = 25
                    rec.invoice_ids = []
                    list = []
                    invoices = self.env['account.invoice'].search(
                        [('res_person', '=', rec.res_person_id.id),('pay_mode', '=','credit')
                         ])
                    if invoices:
                        for line in invoices:
                            if line.state == 'open':
                                list.append([0, 0, {'partner_id': line.partner_id.id,
                                                    'name': line.name,
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
                                                    'invoice_id': line.id
                                                    }
                                             ])
                    rec.invoice_ids = list
            else:
                pass

    # #     -----------------------------
    #
    # @api.onchange('res_person_id', 'partner_id')
    # def onchange_id(self):
    #     for rec in self:
    #         if rec.res_person_id and rec.partner_id:
    #             rec.invoice_ids = []
    #             list = []
    #             invoices = self.env['account.invoice'].search(
    #                 [('partner_id', '=', rec.partner_id.id), ('res_person', '=', rec.res_person_id.id),
    #                  ('packing_slip', '=', False), ('holding_invoice', '=', False)])
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
    #                                             'amount_tax': line.amount_tax,
    #                                             'residual': line.residual,
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

    # @api.depends('res_person_id', 'partner_id')
    # def generate_lines(self):
    #     if self.partner_id and self.res_person_id:
    #         for rec in self:
    #             rec.account_id = 25
    #             rec.invoice_ids = []
    #             list = []
    #             invoices = self.env['account.invoice'].search(
    #                 [('partner_id', '=', rec.partner_id.id),
    #                  ('packing_slip', '=', False), ('holding_invoice', '=', False)])
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
    #     elif self.res_person_id:
    #         for rec in self:
    #             rec.account_id = 25
    #             rec.invoice_ids = []
    #             list = []
    #             invoices = self.env['account.invoice'].search(
    #                 [('res_person', '=', rec.res_person_id.id),
    #                  ('packing_slip', '=', False), ('holding_invoice', '=', False)])
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
    #     elif self.res_person_id and self.partner_id:
    #         for rec in self:
    #             rec.account_id = 25
    #             rec.invoice_ids = []
    #             list = []
    #             invoices = self.env['account.invoice'].search(
    #                 [('partner_id', '=', rec.partner_id.id), ('res_person', '=', rec.res_person_id.id),
    #                  ('packing_slip', '=', False), ('holding_invoice', '=', False)])
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
    @api.multi
    def print_customer_payment_report(self):
        data = self.env['ir.actions.report.xml'].search(
            [('model', '=', 'partner.payment'), ('report_name', '=', 'pharmacy_mgmnt.customer_payment_invoice',)])
        data.download_filename = 'customer payment report.pdf'
        assert len(self) == 1
        self.sent = True
        return self.env['report'].get_action(self, 'pharmacy_mgmnt.customer_payment_invoice')

    # @api.multi
    # @api.onchange("invoice_ids")
    # def onchange_select(self):
    #     for record in self:
    #         if record.payment_amount:
    #             for rec in record.invoice_ids:
    #                 if rec.select == True:
    #                     rec.residual = 0.0

    @api.onchange('invoice_ids')
    def onchange_compute(self):
        for record in self:
            if record.invoice_ids:
                # record.total_amount = sum(line.residual for line in record.invoice_ids)
                record.total_amount = sum(line.residual for line in record.invoice_ids)

    @api.depends('invoice_ids')
    def _compute_value(self):
        for record in self:
            if record.invoice_ids:
                # record.total_amount = sum(line.residual for line in record.invoice_ids) - sum(line.amount_tax for line in record.invoice_ids)
                record.total_amount = sum(line.residual for line in record.invoice_ids)

    @api.depends('total_amount', 'payment_amount')
    def _compute_balance(self):
        for record in self:
            if record.total_amount and record.payment_amount:
                difference = record.total_amount - record.payment_amount
                # if difference < 0:
                # raise osv.except_osv(_('Warning!'), _("Total amount is less than payment amount."))
                record.balance_amount = max(difference, 0.0)

    # @api.multi
    # @api.onchange('payment_amount')
    # def onchange_payment_amt(self):
    #     self.de_residual = self.payment_amount
    #     for record in self.invoice_ids:
    #         if record.select:
    #             amount = 0
    #             invoice = record.invoice_id
    #             if self.de_residual > 0:
    #                 if invoice.residual < self.de_residual:
    #                     amount = invoice.residual
    #                 else:
    #                     amount = self.de_residual
    #                 # self.voucher_relation_id.amount = self.payment_amount
    #                 if amount == invoice.residual:
    #                     invoice.state = 'paid'
    #                     invoice.residual = 0
    #                     invoice.paid_bool = True
    #             else:
    #
    #                 move = self.env['account.move']
    #                 move_line = self.env['account.move.line']
    #
    #                 values5 = {
    #                     'journal_id': 9,
    #                     'date': self.date,
    #                     'tds_id': invoice.id
    #                     # 'period_id': self.period_id.id,623393
    #                 }
    #                 move_id = move.create(values5)
    #                 balance_amount = invoice.residual - payment_amount
    #                 balance_amount += invoice.amount_tax
    #                 values4 = {
    #                     'account_id': 25,
    #                     'name': 'payment for invoice No ' + str(invoice.number2),
    #                     'debit': 0.0,
    #                     'credit': balance_amount,
    #                     'move_id': move_id.id,
    #                     'cheque_no': self.cheque_no,
    #                     'invoice_no_id2': invoice.id,
    #                 }
    #                 line_id1 = move_line.create(values4)
    #
    #                 values6 = {
    #                     'account_id': invoice.account_id.id,
    #                     'name': 'Payment For invoice No ' + str(invoice.number2),
    #                     'debit': balance_amount,
    #                     'credit': 0.0,
    #                     'move_id': move_id.id,
    #                     'cheque_no': self.cheque_no,
    #                     # 'invoice_no_id2': line.bill_no.id,
    #                 }
    #                 line_id2 = move_line.create(values6)
    #
    #                 invoice.move_id = move_id.id
    #                 invoice.move_lines = move_id.line_id.ids
    #                 move_id.button_validate()
    #                 move_id.post()
    #                 name = move_id.name
    #                 self.voucher_relation_id.write({
    #                     'move_id': move_id.id,
    #                     'state': 'posted',
    #                     'number': name,
    #                 })
    #
    #             payment_amount = payment_amount - amount
    #             # self.state = 'paid'
    # payment_records = self.env['account.invoice'].search(
    #     [('partner_id', '=', self.partner_id.id), ('state', '!=', 'draft')])
    # print("records invoice", payment_records)
    # record_count = len(payment_records)
    # count = 0
    # if payment_records:
    #     for rec in payment_records:
    #         if rec.state == 'paid':
    #             count = count + 1
    # if count == record_count:
    #     print("all payments are done")
    #     customer_details = self.env['res.partner'].browse(self.partner_id.id)
    #     if customer_details:
    #         date_today = self.date
    #         x = datetime.strptime(date_today, '%Y-%m-%d')
    #         next_date = x + relativedelta(days=customer_details.days_credit_limit)
    #         cal_date = datetime.strftime(next_date, '%Y-%m-%d')
    #         customer_details.write({'credit_end_date': cal_date})
    #
    # else:
    #     print("there are payments to be completed")

    # return True

    @api.multi
    def action_payment_all(self, context=None):
        if self.payment_amount and self.invoice_ids:
            payment_amount = self.payment_amount
            for record in self.invoice_ids:
                if record.select == True:
                    amount = 0
                    invoice = record.invoice_id
                    if payment_amount > 0:
                        if invoice.residual < payment_amount:
                            amount = invoice.residual
                        else:
                            amount = payment_amount
                        self.voucher_relation_id.amount = self.payment_amount
                        if amount == invoice.residual:
                            invoice.state = 'paid'
                            invoice.paid_bool = True
                        else:

                            move = self.env['account.move']
                            move_line = self.env['account.move.line']

                            values5 = {
                                'journal_id': 9,
                                'date': self.date,
                                'tds_id': invoice.id
                                # 'period_id': self.period_id.id,623393
                            }
                            move_id = move.create(values5)
                            balance_amount = invoice.residual - payment_amount
                            balance_amount += invoice.amount_tax
                            values4 = {
                                'account_id': 25,
                                'name': 'payment for invoice No ' + str(invoice.number),
                                'debit': 0.0,
                                'credit': balance_amount,
                                'move_id': move_id.id,
                                'cheque_no': self.cheque_no,
                                'invoice_no_id2': invoice.id,
                            }
                            line_id1 = move_line.create(values4)

                            values6 = {
                                'account_id': invoice.account_id.id,
                                'name': 'Payment For invoice No ' + str(invoice.number),
                                'debit': balance_amount,
                                'credit': 0.0,
                                'move_id': move_id.id,
                                'cheque_no': self.cheque_no,
                                # 'invoice_no_id2': line.bill_no.id,
                            }
                            line_id2 = move_line.create(values6)

                            invoice.move_id = move_id.id
                            invoice.move_lines = move_id.line_id.ids
                            move_id.button_validate()
                            move_id.post()
                            name = move_id.name
                            self.voucher_relation_id.write({
                                'move_id': move_id.id,
                                'state': 'posted',
                                'number': name,
                            })
                        payment_amount = payment_amount - amount
                        # self.state = 'paid'
            if payment_amount != 0:
                print(payment_amount, 'after first Payment')
                for record in self.invoice_ids:
                    if record.select != True:
                        amount = 0
                        invoice = record.invoice_id
                        if payment_amount > 0:
                            if invoice.residual < payment_amount:
                                amount = invoice.residual
                            else:
                                amount = payment_amount
                            self.voucher_relation_id.amount = self.payment_amount
                            if amount == invoice.residual:
                                invoice.state = 'paid'
                                invoice.paid_bool = True
                            else:

                                move = self.env['account.move']
                                move_line = self.env['account.move.line']

                                values5 = {
                                    'journal_id': 9,
                                    'date': self.date,
                                    'tds_id': invoice.id
                                    # 'period_id': self.period_id.id,623393
                                }
                                move_id = move.create(values5)
                                balance_amount = invoice.residual - payment_amount
                                balance_amount += invoice.amount_tax
                                values4 = {
                                    'account_id': 25,
                                    'name': 'payment for invoice No ' + str(invoice.number),
                                    'debit': 0.0,
                                    'credit': balance_amount,
                                    'move_id': move_id.id,
                                    'cheque_no': self.cheque_no,
                                    'invoice_no_id2': invoice.id,
                                }
                                line_id1 = move_line.create(values4)

                                values6 = {
                                    'account_id': invoice.account_id.id,
                                    'name': 'Payment For invoice No ' + str(invoice.number),
                                    'debit': balance_amount,
                                    'credit': 0.0,
                                    'move_id': move_id.id,
                                    'cheque_no': self.cheque_no,
                                    # 'invoice_no_id2': line.bill_no.id,
                                }
                                line_id2 = move_line.create(values6)

                                invoice.move_id = move_id.id
                                invoice.move_lines = move_id.line_id.ids
                                move_id.button_validate()
                                move_id.post()
                                name = move_id.name
                                self.voucher_relation_id.write({
                                    'move_id': move_id.id,
                                    'state': 'posted',
                                    'number': name,
                                })
                            payment_amount = payment_amount - amount
                            # self.state = 'paid'
            if self.payment_method != "cheque":
                self.advance_amount=payment_amount
            else:
                self.cheque_balance = payment_amount
            payment_records = self.env['account.invoice'].search(
                [('partner_id', '=', self.partner_id.id), ('state', '!=', 'draft')])
            print("records invoice", payment_records)
            record_count = len(payment_records)
            count = 0
            if payment_records:
                for rec in payment_records:
                    if rec.state == 'paid':
                        count = count + 1
            if count == record_count:
                self.state = 'paid'
                print("all payments are done")
                customer_details = self.env['res.partner'].browse(self.partner_id.id)
                if customer_details:
                    date_today = self.date
                    x = datetime.strptime(date_today, '%Y-%m-%d')
                    next_date = x + relativedelta(days=customer_details.days_credit_limit)
                    cal_date = datetime.strftime(next_date, '%Y-%m-%d')
                    customer_details.write({'credit_end_date': cal_date})

            else:
                print("there are payments to be completed")
                self.state = 'paid'

            return True
        else:
            raise ValidationError("Invoice-line or the Payment-Amount is empty!! ")

    @api.multi
    def open_tree_view_history(self, context=None):
        if self.res_person_id:
            field_ids = self.env['account.invoice'].search(
                [('res_person', '=', self.res_person_id.id), ('packing_slip', '=', False),
                 ('holding_invoice', '=', False)]).ids
            domain = [('id', 'in', field_ids)]
            view_id_tree = self.env['ir.ui.view'].search([('name', '=', "model.tree")])
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.invoice',
                'view_type': 'form',
                'view_mode': 'tree,form',
                # 'views': [(view_id_tree[0].id, 'tree'), (False, 'form')],
                'view_id ref="pharmacy_mgmnt.tree_view"': '',
                'target': 'current',
                'domain': domain,
            }

    @api.model
    def create(self, vals):
        # print(vals)
        if not vals.get('reference_number'):
            vals['reference_number'] = self.env['ir.sequence'].next_by_code(
                'partner.payment')
        vals.update({'state': 'draft'})
        vals.update({'account_id': 25})
        result = super(PartnerPayment, self).create(vals)
        if result.payment_amount==0 and self.advance_amount!=0:
            result.payment_amount+=self.advance_amount
        if result.payment_method == 'cheque':
            vals = {
                'name': result.partner_id.id,
                'cheque_no': result.cheque_no,
                't_date': result.date,
                'cheque_amt': result.payment_amount,
                'invoice_ids':  [(4, rec.invoice_id.id, 0) for rec in result.invoice_ids],
                'cheque_date': result.cheque_date,
                'deposit_date': result.deposit_date,
                'clearance_date': result.clearence_date,
                'bank': result.bank,
                'branch': result.branch,
                'ifsc': result.ifsc,
                'state': 'draft'
            }
            cheque = self.env['cheque.entry'].create(vals)
        else:
            pass
        return result


# @api.model
# def create(self, vals):
#     if result.payment_method == 'cheque':
#         print(result.payment_method, '............')
#         # number = self.env['ir.sequence'].next_by_code('cheque.entry.sequence')
#         # print(sequence,',,,,,,,,,,,,,,,,,,,,,,')
#         # cheque = self.env['cheque.entry']
#         vals = {
#             # 's_no': number,
#             'name': result.partner_id.id,
#             'cheque_no': result.cheque_no,
#             't_date': result.date,
#             'cheque_amount': result.payment_amount,
#             # 'invoice_ids': result.invoice_ids,
#             'cheque_date': result.cheque_date,
#             'deposit_date': result.deposit_date,
#             'clearance_date': result.clearence_date,
#             'bank': result.bank,
#             'branch': result.branch,
#             'ifsc': result.ifsc,
#             'state': 'draft'
#         }
#         cheque = self.env['cheque.entry'].create(vals)

# return super(PartnerPayment, self).create(vals)


class AccountInvoiceRefund(models.TransientModel):
    _inherit = 'account.invoice.refund'

    @api.model
    def compute_refund(self, mode='refund'):
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        inv_obj = self.env['account.invoice']
        inv_tax_obj = self.env['account.invoice.tax']
        inv_line_obj = self.env['account.invoice.line']
        context = dict(self._context or {})
        xml_id = False

        for form in self:
            created_inv = []
            date = False
            description = False
            for inv in inv_obj.browse(context.get('active_ids')):
                if inv.state in ['draft', 'proforma2', 'cancel']:
                    pass
                    # raise UserError(_('Cannot refund draft/proforma/cancelled invoice.'))
                if inv.reconciled and mode in ('cancel', 'modify'):
                    pass
                    # raise UserError(_(
                    #     'Cannot refund invoice which is already reconciled, invoice should be unreconciled first. You can only refund this invoice.'))

                date = form.date or False
                description = form.description or inv.name
                refund = inv.refund(form.date_invoice, date, description, inv.journal_id.id)

                created_inv.append(refund.id)
                if inv.picking_transfer_id.code == 'outgoing':
                    data = self.env['stock.picking.type'].search(
                        [('warehouse_id.company_id', '=', company_id), ('code', '=', 'incoming')], limit=1)
                    refund.picking_transfer_id = data.id
                if inv.picking_type_id.code == 'incoming':
                    data = self.env['stock.picking.type'].search(
                        [('warehouse_id.company_id', '=', company_id), ('code', '=', 'outgoing')], limit=1)
                    refund.picking_type_id = data.id
                if mode in ('cancel', 'modify'):
                    movelines = inv.move_id.line_ids
                    to_reconcile_ids = {}
                    to_reconcile_lines = self.env['account.move.line']
                    for line in movelines:
                        if line.account_id.id == inv.account_id.id:
                            to_reconcile_lines += line
                            to_reconcile_ids.setdefault(line.account_id.id, []).append(line.id)
                        if line.reconciled:
                            line.remove_move_reconcile()
                    refund.action_invoice_open()
                    for tmpline in refund.move_id.line_ids:
                        if tmpline.account_id.id == inv.account_id.id:
                            to_reconcile_lines += tmpline
                    to_reconcile_lines.filtered(lambda l: l.reconciled == False).reconcile()
                    if mode == 'modify':
                        invoice = inv.read(inv_obj._get_refund_modify_read_fields())
                        invoice = invoice[0]
                        del invoice['id']
                        invoice_lines = inv_line_obj.browse(invoice['invoice_line'])
                        invoice_lines = inv_obj.with_context(mode='modify')._refund_cleanup_lines(invoice_lines)
                        tax_lines = inv_tax_obj.browse(invoice['tax_line_ids'])
                        tax_lines = inv_obj._refund_cleanup_lines(tax_lines)
                        invoice.update({
                            'type': inv.type,
                            'date_invoice': form.date_invoice,
                            'state': 'draft',
                            'number': False,
                            'invoice_line': invoice_lines,
                            'tax_line_ids': tax_lines,
                            'date': date,
                            'origin': inv.origin,
                            'fiscal_position_id': inv.fiscal_position_id.id,
                        })
                        for field in inv_obj._get_refund_common_fields():
                            if inv_obj._fields[field].type == 'many2one':
                                invoice[field] = invoice[field] and invoice[field][0]
                            else:
                                invoice[field] = invoice[field] or False
                        inv_refund = inv_obj.create(invoice)
                        if inv_refund.payment_term_id.id:
                            inv_refund._onchange_payment_term_date_invoice()
                        created_inv.append(inv_refund.id)
                xml_id = (inv.type in ['out_refund', 'out_invoice']) and 'action_invoice_tree1' or \
                         (inv.type in ['in_refund', 'in_invoice']) and 'action_invoice_tree2'
                # Put the reason in the chatter
                subject = _("Invoice refund")
                body = description
                refund.message_post(body=body, subject=subject)
        if xml_id:
            result = self.env.ref('account.%s' % (xml_id)).read()[0]
            invoice_domain = safe_eval(result['domain'])
            invoice_domain.append(('id', 'in', created_inv))
            result['domain'] = invoice_domain
            return result
        return True
