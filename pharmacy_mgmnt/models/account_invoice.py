# import dateutil.utils
from num2words import num2words

from openerp import api, models, fields
from openerp.osv import osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _, _logger
from openerp.exceptions import except_orm, Warning, RedirectWarning
from datetime import datetime, timedelta
from datetime import date
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class AccountAccountInherit(models.Model):
    _inherit = 'account.account'

    medical = fields.Boolean('Medical')


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    name = fields.Text(string="Description",required=False)
    stock_entry_id = fields.Many2one('entry.stock')
    stock_entry_qty = fields.Float()
    stock_transfer_id = fields.Many2one('stock.transfer')
    # amount_amount = fields.Float('TAX_AMOUNT', compute="_compute_amount_amount")
    amount_amount = fields.Float('TAX_AMOUNT')
    amount_amount1 = fields.Float('Tax_amt', compute="_compute_all", store=True)
    # amount_w_tax = fields.Float('TOTAL_AMT', compute="_compute_amount_with_tax")
    amount_w_tax = fields.Float('Total')
    discount = fields.Float(string='Discount', default=0.0, )
    discount2 = fields.Float("DISCOUNT2")
    discount3 = fields.Float("Dis2(%)", )
    discount4 = fields.Float()
    invoice_id = fields.Many2one('account.invoice',required=False)
    product_tax = fields.Float(compute="_compute_customer_tax")
    unit_price = fields.Float(string='Unit price',compute="_compute_customer_tax")

    @api.model
    def create(self, vals):
        cus_invoice = self.env['account.invoice'].browse(self.env.context.get('active_id'))
        if cus_invoice.type == "out_invoice":
            existing_record = self.search([
                ('invoice_id', '=', vals['invoice_id']),
                ('product_id', '=', vals['product_id']),
                ('expiry_date', '=', vals['expiry_date']),
                ('medicine_rack', '=', vals['medicine_rack']),
                ('product_of', '=', vals['product_of']),
                ('medicine_grp', '=', vals['medicine_grp']),
                ('medicine_name_packing', '=', vals['medicine_name_packing']),
                ('medicine_name_subcat', '=', vals['medicine_name_subcat'])
            ], limit=1)

            if existing_record:
                # If similar record exists, update the quantity field instead of creating a new record
                existing_record.write({
                    'quantity': existing_record.quantity + vals.get('quantity', 0)
                })
                # print(existing_record,'exist')
                return existing_record

        # If no similar record found or incomplete data, create a new record
        result = super(AccountInvoiceLine, self).create(vals)
        if result.invoice_id.type == 'in_invoice' and result.quantity != 0:
            vals = {
                'supplier_id': result.invoice_id.partner_id.id,
                'expiry_date': result.expiry_date,
                'manf_date': result.manf_date,
                'company': result.product_of.id,
                'medicine_1': result.product_id.id,
                'potency': result.medicine_name_subcat.id,
                'medicine_name_packing': result.medicine_name_packing.id,
                'medicine_grp1': result.medicine_grp.id,
                'batch_2': result.batch_2.id,
                'mrp': result.price_unit,
                'qty': result.quantity,
                'rack': result.medicine_rack.id,
                'hsn_code': result.hsn_code,
                'discount': result.discount,
                'invoice_line_tax_id4': result.invoice_line_tax_id4,
                'stock_date': date.today(),
            }
            print(date.today())
            stock_entry = self.env['entry.stock'].create(vals)
            result.stock_entry_id = stock_entry.id

        if result.invoice_id.type == 'out_invoice' and result.invoice_id.state == 'packing_slip':
            domain = [
                ('medicine_1', '=', result.product_id.id),
                ('expiry_date', '=', result.expiry_date),
                ('rack', '=', result.medicine_rack.id),
                ('company', '=', result.product_of.id),
                ('medicine_grp1', '=', result.medicine_grp.id),
                ('medicine_name_packing', '=', result.medicine_name_packing.id),
                ('potency', '=', result.medicine_name_subcat.id)
            ]

            entry_stock_ids = self.env['entry.stock'].search(domain, order='id desc')
            if not entry_stock_ids or sum(entry_stock_ids.mapped('qty')) <= 0:
                raise Warning(_('Product with current combination is not available in stock'))

            stock_transfer_id = self.env['stock.transfer'].create({
                'partner_id': result.invoice_id.partner_id.id,
                'title': result.invoice_id.cus_title_1.id,
                'product_id': result.product_id.id,
                'product_uom_qty': result.quantity,
                'date': result.invoice_id.date_invoice
            })
            quantity = result.quantity
            result.stock_transfer_id = stock_transfer_id.id
            stock_entry_qty = 0
            for stock in entry_stock_ids:
                if stock.qty >= quantity:
                    stock.write({
                        'qty': stock.qty - quantity,
                    })
                    stock_entry_qty += quantity
                    break
                else:
                    stock.write({
                        'qty': 0
                    })
                    stock_entry_qty += stock.qty
                quantity -= stock.qty
            result.stock_entry_qty = stock_entry_qty

        return result

    @api.multi
    def write(self, vals):
        for rec in self:
            if rec.invoice_id.type == 'out_invoice':
                # list_keys = ['product_id', 'expiry_date', 'medicine_rack',
                #              'product_of', 'medicine_grp', 'medicine_name_packing',
                #              'medicine_name_subcat', 'quantity', 'hsn_code']

                # if vals.get('packing_slip') or self.state not in ['draft', 'holding_invoice']:
                if vals.get('packing_slip') or rec.invoice_id.state == 'packing_slip':
                    list_item = ['product_id', 'expiry_date', 'medicine_rack', 'product_of', 'medicine_grp',
                                 'medicine_name_packing', 'medicine_name_subcat', 'quantity', 'hsn_code']
                    flag = 0
                    for item in list_item:
                        if vals.get(item):
                            flag = 1
                    if flag:
                        if vals.get('quantity'):
                            quantity = vals.get('quantity')
                            rec.stock_transfer_id.product_uom_qty = vals.get('quantity')
                        else:
                            quantity = rec.quantity

                        domain = [('qty', '>=', quantity)]
                        if vals.get('product_id'):
                            domain += [('medicine_1', '=', vals.get('product_id'))]
                        else:
                            if rec.product_id:
                                domain += [('medicine_1', '=', rec.product_id.id)]

                        if vals.get('expiry_date'):
                            domain += [('medicine_1', '=', vals.get('expiry_date'))]
                        else:
                            if rec.expiry_date:
                                domain += [('expiry_date', '=', rec.expiry_date)]

                        if vals.get('medicine_rack'):
                            domain += [('medicine_1', '=', vals.get('medicine_rack'))]
                        else:
                            if rec.medicine_rack:
                                domain += [('rack', '=', rec.medicine_rack.id)]

                        if vals.get('product_of'):
                            domain += [('medicine_1', '=', vals.get('product_of'))]
                        else:
                            if rec.product_of:
                                domain += [('company', '=', rec.product_of.id)]

                        if vals.get('medicine_grp'):
                            domain += [('medicine_1', '=', vals.get('medicine_grp'))]
                        else:
                            if rec.medicine_grp:
                                domain += [('medicine_grp1', '=', rec.medicine_grp.id)]

                        if vals.get('medicine_name_packing'):
                            domain += [('medicine_1', '=', vals.get('medicine_name_packing'))]
                        else:
                            if rec.medicine_name_packing:
                                domain += [('medicine_name_packing', '=', rec.medicine_name_packing.id)]

                        if vals.get('medicine_name_subcat'):
                            domain += [('medicine_1', '=', vals.get('medicine_name_subcat'))]
                        else:
                            if rec.medicine_name_subcat:
                                domain += [('potency', '=', rec.medicine_name_subcat.id)]

                        if vals.get('hsn_code'):
                            domain += [('medicine_1', '=', vals.get('hsn_code'))]
                        else:
                            if rec.hsn_code:
                                domain += [('hsn_code', '=', rec.hsn_code)]
                        # domain += [('qty', '=', 0)]
                        entry_stock_ids = rec.env['entry.stock'].search(domain, order='id asc', limit=1)
                        if sum(entry_stock_ids.mapped('qty')) <= 0 or not entry_stock_ids:
                            if vals.get('medicine_rack'):
                                domain.remove(('rack', '=', vals.get('medicine_rack')))
                            if rec.medicine_rack:
                                domain.remove(('rack', '=', rec.medicine_rack.id))
                            if rec.expiry_date:
                                domain.remove(('expiry_date', '=', rec.expiry_date))
                            if vals.get('expiry_date'):
                                domain.remove(('expiry_date', '=', vals.get('expiry_date')))
                            entry_stock_ids = rec.env['entry.stock'].search(domain, order='id asc')
                        if not entry_stock_ids:
                            domain.remove(('qty', '>=', quantity))
                            domain += [('qty', '>=', 0)]
                            entry_stock_ids = rec.env['entry.stock'].search(domain, order='id asc')

                        if sum(entry_stock_ids.mapped('qty')) <= 0 or not entry_stock_ids:
                            raise Warning(
                                _('Only we have %s Products with current combination in stock') % str(
                                    int(rec.stock_entry_qty) + int(sum(entry_stock_ids.mapped('qty')))))
                        quantity_comp = quantity
                        inverse = False
                        if rec.stock_entry_qty < quantity:
                            quantity_comp = vals.get('quantity') - rec.stock_entry_qty
                        else:
                            quantity_comp = rec.stock_entry_qty - vals.get('quantity')
                            inverse = True
                        for stock in entry_stock_ids:
                            if quantity_comp > 0:
                                if stock.qty >= quantity_comp:
                                    if inverse:
                                        stock.write({
                                            'qty': abs(stock.qty + quantity_comp),
                                        })
                                    else:
                                        stock.write({
                                            'qty': abs(stock.qty - quantity_comp),
                                        })
                                    # quantity -= stock.qty
                                    break
                                else:
                                    quantity_comp = (quantity_comp - stock.qty)
                                    stock.write({
                                        'qty': 0
                                    })
                        vals['stock_entry_qty'] = quantity
            res = super(AccountInvoiceLine, rec).write(vals)
            if rec.invoice_id.type == 'in_invoice':
                vals = {
                    'expiry_date': rec.expiry_date,
                    'manf_date': rec.manf_date,
                    'company': rec.product_of.id,
                    'medicine_1': rec.product_id.id,
                    'potency': rec.medicine_name_subcat.id,
                    'medicine_name_packing': rec.medicine_name_packing.id,
                    'medicine_grp1': rec.medicine_grp.id,
                    'batch_2': rec.batch_2.id,
                    'mrp': rec.price_unit,
                    'qty': rec.quantity,
                    'rack': rec.medicine_rack.id,
                    'hsn_code': rec.hsn_code,
                    'discount': rec.discount,
                    'invoice_line_tax_id4': rec.invoice_line_tax_id4,
                }
                result = rec.stock_entry_id.update(vals)
            return res

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.invoice_id.state in ['draft', 'holding_invoice', 'packing_slip']:
                if rec.invoice_id.type == 'in_invoice':
                    if rec.stock_entry_id:
                        rec.stock_entry_id.unlink()
                if rec.invoice_id.type == 'out_invoice':
                    if rec.invoice_id.packing_slip:
                        if rec.stock_entry_qty:
                            domain = []
                            if rec.product_id:
                                domain += [('medicine_1', '=', rec.product_id.id)]
                            if rec.expiry_date:
                                domain += [('expiry_date', '=', rec.expiry_date)]
                            if rec.medicine_rack:
                                domain += [('rack', '=', rec.medicine_rack.id)]
                            if rec.product_of:
                                domain += [('company', '=', rec.product_of.id)]
                            if rec.medicine_grp:
                                domain += [('medicine_grp1', '=', rec.medicine_grp.id)]
                            if rec.medicine_name_packing:
                                domain += [('medicine_name_packing', '=', rec.medicine_name_packing.id)]
                            if rec.medicine_name_subcat:
                                domain += [('potency', '=', rec.medicine_name_subcat.id)]

                            entry_stock_id = self.env['entry.stock'].search(domain, order='id desc', limit=1)
                            if not entry_stock_id:
                                if rec.medicine_rack:
                                    domain -= [('rack', '=', self.medicine_rack.id)]
                                    entry_stock_id = self.env['entry.stock'].search(domain, order='id desc', limit=1)
                            entry_stock_id.write({
                                'qty': entry_stock_id.qty + rec.quantity,
                            })
            else:
                raise Warning("Only Draft Invoice Lines can be deleted")
        return super(AccountInvoiceLine, self).unlink()

    # CALCULATE CATEGORY DISCOUNT-CUSTOMER INVOICE
    @api.one
    @api.depends('discount', 'calc')
    def _compute_mass_discount(self):
        if self.invoice_id.discount_rate == 0:
            pass
        # else:
        #     if self.discount == 0:
        #         discount_rate = self.invoice_id.discount_rate
        #         self.discount = discount_rate

    @api.model
    def move_line_get_item(self, line):
        total_price = 0
        if line.invoice_id.type == 'out_invoice':
            # total_price = line.amt_w_tax
            total_price = round(line.price_subtotal)
        if line.invoice_id.type != 'out_invoice':
            # total_price = line.amount_w_tax
            discount = line.quantity * line.price_unit * (line.discount / 100)
            amount = (line.quantity * line.price_unit) - discount
            tax_amount = amount * (line.invoice_line_tax_id4 / 100)
            total_price = round(tax_amount + line.rate_amt)

        return {
            'type': 'src',
            'name': line.name,
            'price_unit': line.price_unit,
            'quantity': line.quantity,
            'price': total_price,
            'account_id': line.account_id.id,
            'product_id': line.product_id.id,
            'uos_id': line.uos_id.id,
            'account_analytic_id': line.account_analytic_id.id,
            'taxes': line.invoice_line_tax_id,
        }

    # @api.model
    # def move_line_get(self, invoice_id):
    #     res = []
    #     self._cr.execute(
    #         'SELECT * FROM account_invoice_tax WHERE invoice_id = %s',
    #         (invoice_id,)
    #     )
    #     for row in self._cr.dictfetchall():
    #         if not (row['amount'] or row['tax_code_id'] or row['tax_amount']):
    #             continue
    #         res.append({
    #             'type': 'tax',
    #             'name': row['name'],
    #             'price_unit': row['amount'],
    #             'quantity': 1,
    #             'price': row['amount'] or 0.0,
    #             'account_id': row['account_id'],
    #             'tax_code_id': row['tax_code_id'],
    #             'tax_amount': row['tax_amount'],
    #             'account_analytic_id': row['account_analytic_id'],
    #         })
    #     return res

    # CUSTOMER TAX CALCULATION
    @api.model
    @api.depends('amt_w_tax', 'invoice_line_tax_id4', 'price_subtotal', 'amount_amount1', 'price_unit', 'rate_amtc','product_tax','unit_price')
    def _compute_customer_tax(self):
        for record in self:
            if record.partner_id.customer:
                for rec in record:
                    if rec.rate_amtc == 0:
                        if rec.rate_amtc < rec.price_subtotal:
                            if rec.rate_amtc == 0:
                                rate_amount = rec.price_subtotal
                                quantity = rec.quantity
                                per_product = rate_amount/ quantity
                                perce = rec.invoice_line_tax_id4
                                tax_amount = perce * 100 / (perce + 100)
                                tax = per_product * tax_amount/100
                                rec.product_tax = tax * quantity
                                rec.unit_price = per_product - tax
                                # tax = rate_amount * (perce / 100)
                                rec.amt_tax = round(rec.product_tax)
                                # total = rate_amount - round(tax)
                                rec.amt_w_tax = rec.price_subtotal
                                rec.amount_residual = rec.price_subtotal
                                rec.amount_residual_currency = rec.price_subtotal

                    else:
                        rate_amount = rec.price_subtotal
                        quantity = rec.quantity
                        per_product = rate_amount / quantity
                        perce = rec.invoice_line_tax_id4
                        tax_amount = perce * 100 / (perce + 100)
                        tax = per_product * tax_amount / 100
                        rec.product_tax = tax * quantity
                        rec.unit_price = per_product - tax
                        rec.amt_tax = round(rec.product_tax)
                        rec.amt_w_tax = rec.price_subtotal
                        rec.amount_residual = rec.price_subtotal
                        rec.amount_residual_currency = rec.price_subtotal
                        # perce = rec.invoice_line_tax_id4
                        # new_rate = rec.rate_amtc
                        # tax = new_rate * (perce / 100)
                        # rec.amt_tax = round(tax)
                        # total = new_rate + round(tax)
                        # rec.amt_w_tax = total

    @api.one
    @api.depends('product_id', 'medicine_name_subcat', 'medicine_grp', 'medicine_name_subcat', 'discount2',
                 'price_unit',
                 'quantity', 'discount')
    def _compute_all(self):
        if self.partner_id.supplier == True:
            # FETCH DISCOUNT1
            for rec in self:
                flag = 0
                s_obj = self.env['supplier.discounts'].search([('supplier', '=', rec.partner_id.id)])
                if s_obj:
                    for lines in s_obj.lines:
                        if (lines.company.id == rec.product_of.id):
                            if (lines.medicine_1.id == rec.product_id.id):
                                if (lines.potency.id == rec.medicine_name_subcat.id):
                                    if (lines.medicine_grp1.medicine_grp.id == rec.medicine_grp.id):
                                        if (lines.medicine_name_packing.id == rec.medicine_name_packing.id):
                                            rec.discount = lines.discount
                                            flag = 1
                        if flag == 1:
                            pass
                        else:

                            # print("Search in 2nd model")
                            s_obj = self.env['supplier.discounts'].search([('supplier', '=', rec.partner_id.id)])
                            if s_obj:
                                for lines in s_obj.lines2:
                                    if (lines.company.id == rec.product_of.id):
                                        # if (lines.medicine_1.id == rec.product_id.id):
                                        if (lines.potency.id == rec.medicine_name_subcat.id):
                                            if (lines.medicine_grp1.id == rec.medicine_grp.id):
                                                if (lines.medicine_name_packing.id == rec.medicine_name_packing.id):
                                                    rec.discount = lines.discount
                                                    print("success")

                                    # if ((lines.company.id == rec.product_of.id) and (
                                    #         lines.medicine_grp1.id == rec.medicine_grp.id) and (
                                    #         lines.medicine_1.id == None) and (
                                    #         lines.potency.id == rec.medicine_name_subcat.id) and (
                                    #         lines.medicine_name_packing.id == rec.medicine_name_packing.id)):
                                    #     rec.discount = lines.discount
                                    # else:
                                    if ((lines.company.id == rec.product_of.id) and (
                                            lines.medicine_grp1.id == rec.medicine_grp.id)
                                            and (
                                                    lines.potency.id == rec.medicine_name_subcat.id) and (
                                                    lines.medicine_name_packing.id == None)):
                                        rec.discount = lines.discount
                                    else:
                                        if ((lines.company.id == rec.product_of.id) and (
                                                lines.medicine_grp1.id == rec.medicine_grp.id) and (
                                                lines.potency.id == None) and (
                                                lines.medicine_name_packing.id == rec.medicine_name_packing.id)):
                                            rec.discount = lines.discount
                                        else:
                                            if ((lines.company.id == rec.product_of.id) and (
                                                    lines.medicine_grp1.id == rec.medicine_grp.id) and (
                                                    lines.potency.id == None) and (
                                                    lines.medicine_name_packing.id == None)):
                                                rec.discount = lines.discount
                                            if ((lines.company.id == rec.product_of.id) and (
                                                    lines.medicine_name_packing.id == None) and (
                                                    lines.potency.id == None) and (
                                                    lines.medicine_grp1.id == rec.medicine_grp.id)):
                                                rec.discount = lines.discount
                                            if ((lines.company.id == None) and (
                                                    lines.medicine_name_packing.id == rec.medicine_name_packing.id) and (
                                                    lines.potency.id == rec.medicine_name_subcat.id) and (
                                                    lines.medicine_grp1.id == None)):
                                                rec.discount = lines.discount
                                            if ((lines.company.id == None) and (
                                                    lines.medicine_name_packing.id == None) and (
                                                    lines.potency.id == None) and (
                                                    lines.medicine_grp1.id == rec.medicine_grp.id)):
                                                rec.discount = lines.discount
                                            if ((lines.company.id == None) and (
                                                    lines.medicine_name_packing.id == None) and (
                                                    lines.potency.id == rec.medicine_name_subcat.id) and (
                                                    lines.medicine_grp1.id == None)):
                                                rec.discount = lines.discount
                                            if ((lines.company.id == None) and (
                                                    lines.medicine_name_packing.id == rec.medicine_name_packing.id) and (
                                                    lines.potency.id == None) and (lines.medicine_grp1.id == None)):
                                                rec.discount = lines.discount

            # FETCH EXTRA DDISCOUNT
            if self.medicine_grp:
                dis_obj = self.env['group.discount'].search([('medicine_grp.medicine_grp', '=', self.medicine_grp.id),
                                                             (
                                                                 'medicine_name_subcat', '=',
                                                                 self.medicine_name_subcat.id),
                                                             ('medicine_name_packing', '=',
                                                              self.medicine_name_packing.id)])
                if dis_obj:
                    varia = dis_obj.discount
                    self.discount3 = dis_obj.discount
                    if dis_obj.expiry_months:
                        if self.manf_date:
                            text = self.manf_date
                            x = datetime.strptime(text, '%Y-%m-%d')
                            nextday_date = x + relativedelta(months=dis_obj.expiry_months)
                            cal_date = datetime.strftime(nextday_date, '%Y-%m-%d')
                            # print("calculated date............", cal_date)
                            self.expiry_date = cal_date
                            # self.write({'expiry_date': cal_date})
                else:
                    dis_obj2 = self.env['group.discount'].search([('medicine_grp', '=', self.medicine_grp.id),
                                                                  ('medicine_name_subcat', '=',
                                                                   self.medicine_name_subcat.id),
                                                                  ('medicine_name_packing', '=', None)])

                    if dis_obj2:
                        self.discount3 = dis_obj2.discount
                        if dis_obj2.expiry_months:
                            if self.manf_date:
                                text = self.manf_date
                                x = datetime.strptime(text, '%Y-%m-%d')
                                nextday_date = x + relativedelta(months=dis_obj2.expiry_months)
                                cal_date = datetime.strftime(nextday_date, '%Y-%m-%d')
                                self.expiry_date = cal_date
                                # self.write({'expiry_date': cal_date})
                    else:
                        dis_obj4 = self.env['group.discount'].search([('medicine_grp', '=', self.medicine_grp.id),
                                                                      ('medicine_name_subcat', '=', None),
                                                                      ('medicine_name_packing', '=',
                                                                       self.medicine_name_packing.id)])
                        if dis_obj4:
                            self.discount3 = dis_obj4.discount
                            if dis_obj4.expiry_months:
                                if self.manf_date:
                                    text = self.manf_date
                                    x = datetime.strptime(text, '%Y-%m-%d')
                                    nextday_date = x + relativedelta(months=dis_obj4.expiry_months)
                                    cal_date = datetime.strftime(nextday_date, '%Y-%m-%d')
                                    self.expiry_date = cal_date
                                    # self.write({'expiry_date': cal_date})


                        else:
                            dis_obj3 = self.env['group.discount'].search([('medicine_grp', '=', self.medicine_grp.id),
                                                                          ('medicine_name_subcat', '=', None),
                                                                          ('medicine_name_packing', '=', None)])
                            if dis_obj3:
                                self.discount3 = dis_obj3.discount
                                if dis_obj3.expiry_months:
                                    if self.manf_date:
                                        text = self.manf_date
                                        x = datetime.strptime(text, '%Y-%m-%d')
                                        nextday_date = x + relativedelta(months=dis_obj3.expiry_months)
                                        cal_date = datetime.strftime(nextday_date, '%Y-%m-%d')
                                        self.expiry_date = cal_date
                                        # self.write({'expiry_date': cal_date})

            # TAX CALCULATION AND SUBTOTAL WITH 2 DISCOUNTS IF THERE IS DISCOUNT1 AND DISCOUNT2
            if self.price_unit:
                # print("price unit exist")
                subtotal_wo_dis1 = self.price_unit * self.quantity
                if self.discount:
                    # print("first discount exist")
                    if self.discount3:
                        # print("condition-extra discount")
                        discount1_amount = subtotal_wo_dis1 * (self.discount / 100)
                        item = self.invoice_line_tax_id4
                        subtotal_with_dis1 = subtotal_wo_dis1 - discount1_amount
                        tax_amount = subtotal_with_dis1 * (item / 100)
                        # self.price_subtotal = subtotal_with_dis1
                        self.amount_amount1 = tax_amount
                        # self.amount_w_tax = subtotal_with_dis1 + tax_amount
                        dis2_amt = subtotal_with_dis1 * (self.discount3 / 100)
                        subtotal_with_dis2 = subtotal_with_dis1 - dis2_amt
                        # print("1st round of calculation")
                        self.price_subtotal = subtotal_with_dis2
                        self.amount_w_tax = subtotal_with_dis2 + tax_amount
                        self.grand_total = subtotal_with_dis2 + tax_amount
                        # print("price_subtotal", subtotal_with_dis2)
                        # print("total", subtotal_with_dis2 + tax_amount)
                        # print("extra dis", dis2_amt)
                        self.price_subtotal = self.amount_w_tax - self.amount_amount1
                        self.dis1 = discount1_amount
                        self.dis2 = dis2_amt


                    else:
                        discount1_amount = subtotal_wo_dis1 * (self.discount / 100)
                        item = self.invoice_line_tax_id4
                        subtotal_with_dis1 = subtotal_wo_dis1 - discount1_amount
                        tax_amount = subtotal_with_dis1 * (item / 100)
                        self.price_subtotal = subtotal_with_dis1
                        self.amount_amount1 = tax_amount
                        self.amount_w_tax = subtotal_with_dis1 + tax_amount
                        self.grand_total = subtotal_with_dis1 + tax_amount
                        self.dis1 = discount1_amount
                else:
                    item = self.invoice_line_tax_id4
                    tax_amount = subtotal_wo_dis1 * (item / 100)
                    self.amount_amount1 = tax_amount
                    self.amount_w_tax = subtotal_wo_dis1 + tax_amount
                    self.grand_total = subtotal_wo_dis1 + tax_amount
        if self.partner_id.supplier == True:
            self.rate_amt = self.amount_w_tax - self.amount_amount1
            # self.grand_total = self.amount_w_tax - self.amount_amount1
            # print("finallyyyyy", self.rate_amt)

    # @api.one
    # @api.depends('product_id', 'medicine_name_subcat', 'medicine_grp', 'medicine_name_subcat', 'discount2',
    #              'price_unit',
    #              'quantity', 'discount')
    # def _compute_all(self):
    #     if self.partner_id.supplier == True:
    #         # FETCH DISCOUNT1
    #         for rec in self:
    #             flag = 0
    #             s_obj = self.env['supplier.discounts'].search([('supplier', '=', rec.partner_id.id)])
    #             if s_obj:
    #                 for lines in s_obj.lines:
    #                     if (lines.company.id == rec.product_of.id):
    #                         if (lines.medicine_1.id == rec.product_id.id):
    #                             if (lines.potency.id == rec.medicine_name_subcat.id):
    #                                 if (lines.medicine_grp1.id == rec.medicine_grp.id):
    #                                     if (lines.medicine_name_packing.id == rec.medicine_name_packing.id):
    #                                         rec.discount = lines.discount
    #                                         flag = 1
    #                     if flag == 1:
    #                         pass
    #                     else:
    #
    #                         # print("Search in 2nd model")
    #                         s_obj = self.env['supplier.discounts2'].search([('supplier', '=', rec.partner_id.id)])
    #                         if s_obj:
    #                             for lines in s_obj.lines:
    #                                 if (lines.company.id == rec.product_of.id):
    #                                     # if (lines.medicine_1.id == rec.product_id.id):
    #                                     if (lines.potency.id == rec.medicine_name_subcat.id):
    #                                         if (lines.medicine_grp1.id == rec.medicine_grp.id):
    #                                             if (lines.medicine_name_packing.id == rec.medicine_name_packing.id):
    #                                                 rec.discount = lines.discount
    #                                                 print("success")
    #
    #                                 # if ((lines.company.id == rec.product_of.id) and (
    #                                 #         lines.medicine_grp1.id == rec.medicine_grp.id) and (
    #                                 #         lines.medicine_1.id == None) and (
    #                                 #         lines.potency.id == rec.medicine_name_subcat.id) and (
    #                                 #         lines.medicine_name_packing.id == rec.medicine_name_packing.id)):
    #                                 #     rec.discount = lines.discount
    #                                 # else:
    #                                 if ((lines.company.id == rec.product_of.id) and (
    #                                         lines.medicine_grp1.id == rec.medicine_grp.id)
    #                                         and (
    #                                                 lines.potency.id == rec.medicine_name_subcat.id) and (
    #                                                 lines.medicine_name_packing.id == None)):
    #                                     rec.discount = lines.discount
    #                                 else:
    #                                     if ((lines.company.id == rec.product_of.id) and (
    #                                             lines.medicine_grp1.id == rec.medicine_grp.id) and (
    #                                             lines.potency.id == None) and (
    #                                             lines.medicine_name_packing.id == rec.medicine_name_packing.id)):
    #                                         rec.discount = lines.discount
    #                                     else:
    #                                         if ((lines.company.id == rec.product_of.id) and (
    #                                                 lines.medicine_grp1.id == rec.medicine_grp.id) and (
    #                                                 lines.potency.id == None) and (
    #                                                 lines.medicine_name_packing.id == None)):
    #                                             rec.discount = lines.discount
    #                                         if ((lines.company.id == rec.product_of.id) and (
    #                                                 lines.medicine_name_packing.id == None) and (
    #                                                 lines.potency.id == None) and (
    #                                                 lines.medicine_grp1.id == rec.medicine_grp.id)):
    #                                             rec.discount = lines.discount
    #                                         if ((lines.company.id == None) and (
    #                                                 lines.medicine_name_packing.id == rec.medicine_name_packing.id) and (
    #                                                 lines.potency.id == rec.medicine_name_subcat.id) and (
    #                                                 lines.medicine_grp1.id == None)):
    #                                             rec.discount = lines.discount
    #                                         if ((lines.company.id == None) and (
    #                                                 lines.medicine_name_packing.id == None) and (
    #                                                 lines.potency.id == None) and (
    #                                                 lines.medicine_grp1.id == rec.medicine_grp.id)):
    #                                             rec.discount = lines.discount
    #                                         if ((lines.company.id == None) and (
    #                                                 lines.medicine_name_packing.id == None) and (
    #                                                 lines.potency.id == rec.medicine_name_subcat.id) and (
    #                                                 lines.medicine_grp1.id == None)):
    #                                             rec.discount = lines.discount
    #                                         if ((lines.company.id == None) and (
    #                                                 lines.medicine_name_packing.id == rec.medicine_name_packing.id) and (
    #                                                 lines.potency.id == None) and (lines.medicine_grp1.id == None)):
    #                                             rec.discount = lines.discount
    #
    #         # FETCH EXTRA DDISCOUNT
    #         if self.medicine_grp:
    #             dis_obj = self.env['group.discount'].search([('medicine_grp', '=', self.medicine_grp.id),
    #                                                          (
    #                                                              'medicine_name_subcat', '=',
    #                                                              self.medicine_name_subcat.id),
    #                                                          ('medicine_name_packing', '=',
    #                                                           self.medicine_name_packing.id)])
    #             if dis_obj:
    #                 varia = dis_obj.discount
    #                 self.discount3 = dis_obj.discount
    #                 if dis_obj.expiry_months:
    #                     if self.manf_date:
    #                         text = self.manf_date
    #                         x = datetime.strptime(text, '%Y-%m-%d')
    #                         nextday_date = x + relativedelta(months=dis_obj.expiry_months)
    #                         cal_date = datetime.strftime(nextday_date, '%Y-%m-%d')
    #                         # print("calculated date............", cal_date)
    #                         self.expiry_date = cal_date
    #                         # self.write({'expiry_date': cal_date})
    #             else:
    #                 dis_obj2 = self.env['group.discount'].search([('medicine_grp', '=', self.medicine_grp.id),
    #                                                               ('medicine_name_subcat', '=',
    #                                                                self.medicine_name_subcat.id),
    #                                                               ('medicine_name_packing', '=', None)])
    #
    #                 if dis_obj2:
    #                     self.discount3 = dis_obj2.discount
    #                     if dis_obj2.expiry_months:
    #                         if self.manf_date:
    #                             text = self.manf_date
    #                             x = datetime.strptime(text, '%Y-%m-%d')
    #                             nextday_date = x + relativedelta(months=dis_obj2.expiry_months)
    #                             cal_date = datetime.strftime(nextday_date, '%Y-%m-%d')
    #                             self.expiry_date = cal_date
    #                             # self.write({'expiry_date': cal_date})
    #                 else:
    #                     dis_obj4 = self.env['group.discount'].search([('medicine_grp', '=', self.medicine_grp.id),
    #                                                                   ('medicine_name_subcat', '=', None),
    #                                                                   ('medicine_name_packing', '=',
    #                                                                    self.medicine_name_packing.id)])
    #                     if dis_obj4:
    #                         self.discount3 = dis_obj4.discount
    #                         if dis_obj4.expiry_months:
    #                             if self.manf_date:
    #                                 text = self.manf_date
    #                                 x = datetime.strptime(text, '%Y-%m-%d')
    #                                 nextday_date = x + relativedelta(months=dis_obj4.expiry_months)
    #                                 cal_date = datetime.strftime(nextday_date, '%Y-%m-%d')
    #                                 self.expiry_date = cal_date
    #                                 # self.write({'expiry_date': cal_date})
    #
    #
    #                     else:
    #                         dis_obj3 = self.env['group.discount'].search([('medicine_grp', '=', self.medicine_grp.id),
    #                                                                       ('medicine_name_subcat', '=', None),
    #                                                                       ('medicine_name_packing', '=', None)])
    #                         if dis_obj3:
    #                             self.discount3 = dis_obj3.discount
    #                             if dis_obj3.expiry_months:
    #                                 if self.manf_date:
    #                                     text = self.manf_date
    #                                     x = datetime.strptime(text, '%Y-%m-%d')
    #                                     nextday_date = x + relativedelta(months=dis_obj3.expiry_months)
    #                                     cal_date = datetime.strftime(nextday_date, '%Y-%m-%d')
    #                                     self.expiry_date = cal_date
    #                                     # self.write({'expiry_date': cal_date})
    #
    #         # TAX CALCULATION AND SUBTOTAL WITH 2 DISCOUNTS IF THERE IS DISCOUNT1 AND DISCOUNT2
    #         if self.price_unit:
    #             # print("price unit exist")
    #             subtotal_wo_dis1 = self.price_unit * self.quantity
    #             if self.discount:
    #                 # print("first discount exist")
    #                 if self.discount3:
    #                     # print("condition-extra discount")
    #                     discount1_amount = subtotal_wo_dis1 * (self.discount / 100)
    #                     item = self.invoice_line_tax_id4
    #                     subtotal_with_dis1 = subtotal_wo_dis1 - discount1_amount
    #                     tax_amount = subtotal_with_dis1 * (item / 100)
    #                     # self.price_subtotal = subtotal_with_dis1
    #                     self.amount_amount1 = tax_amount
    #                     # self.amount_w_tax = subtotal_with_dis1 + tax_amount
    #                     dis2_amt = subtotal_with_dis1 * (self.discount3 / 100)
    #                     subtotal_with_dis2 = subtotal_with_dis1 - dis2_amt
    #                     # print("1st round of calculation")
    #                     self.price_subtotal = subtotal_with_dis2
    #                     self.amount_w_tax = subtotal_with_dis2 + tax_amount
    #                     self.grand_total = subtotal_with_dis2 + tax_amount
    #                     # print("price_subtotal", subtotal_with_dis2)
    #                     # print("total", subtotal_with_dis2 + tax_amount)
    #                     # print("extra dis", dis2_amt)
    #                     self.price_subtotal = self.amount_w_tax - self.amount_amount1
    #                     self.dis1 = discount1_amount
    #                     self.dis2 = dis2_amt
    #
    #
    #                 else:
    #                     discount1_amount = subtotal_wo_dis1 * (self.discount / 100)
    #                     item = self.invoice_line_tax_id4
    #                     subtotal_with_dis1 = subtotal_wo_dis1 - discount1_amount
    #                     tax_amount = subtotal_with_dis1 * (item / 100)
    #                     self.price_subtotal = subtotal_with_dis1
    #                     self.amount_amount1 = tax_amount
    #                     self.amount_w_tax = subtotal_with_dis1 + tax_amount
    #                     self.grand_total = subtotal_with_dis1 + tax_amount
    #                     self.dis1 = discount1_amount
    #             else:
    #                 item = self.invoice_line_tax_id4
    #                 tax_amount = subtotal_wo_dis1 * (item / 100)
    #                 self.amount_amount1 = tax_amount
    #                 self.amount_w_tax = subtotal_wo_dis1 + tax_amount
    #                 self.grand_total = subtotal_wo_dis1 + tax_amount
    #     if self.partner_id.supplier == True:
    #         self.rate_amt = self.amount_w_tax - self.amount_amount1
    #         # self.grand_total = self.amount_w_tax - self.amount_amount1
    #         # print("finallyyyyy", self.rate_amt)
    #
    # CUSTOMER EXTRA DISCOUNT

    @api.one
    @api.depends('product_id', 'medicine_name_subcat', 'medicine_grp', 'medicine_name_subcat', 'discount3',
                 'price_unit',
                 'quantity', 'amt_w_tax')
    def _compute_cus_ex_discount(self):
        for record in self:

            percentage = 0
            if record.partner_id.customer == True:
                if record.rate_amtc:
                    for rec in self:
                        # print("got")
                        new_rate = rec.rate_amtc
                        percentage = (new_rate / rec.price_subtotal) * 100
                        rec.new_disc = 100 - percentage

    medicine_rack = fields.Many2one('product.medicine.types', 'Rack')
    product_of = fields.Many2one('product.medicine.responsible', 'Company')
    medicine_name_subcat = fields.Many2one('product.medicine.subcat', 'Potency',required=True)
    medicine_name_packing = fields.Many2one('product.medicine.packing', 'Pack', )

    # medicine_grp = fields.Many2one('product.medicine.group', 'GROUP',compute='_compute_taxes',readonly="0")
    medicine_grp = fields.Many2one('product.medicine.group', 'Grp', )

    # medicine_group = fields.Char('Group', related="product_id.medicine_group")
    batch = fields.Char("BATCH", related="product_id.batch")
    batch_2 = fields.Many2one('med.batch', "Batch", )
    # test = fields.Float('Test', compute="_get_sup_discount_amt")
    test = fields.Float('Test')
    # test2 = fields.Float('Test2',compute="_get_sup_discount2")
    test2 = fields.Float('Test2')
    test3 = fields.Float('Test3', compute="_compute_all")
    expiry_date = fields.Date(string='Exp')
    manf_date = fields.Date(string='Mfd')
    alert_date = fields.Date(string='Alert Date')
    avail_qty = fields.Float(string='Stock Total', related="product_id.qty_available")
    hsn_code = fields.Char('Hsn')
    # invoice_line_tax_id3 = fields.Many2one('tax.combo', string='Gst')
    invoice_line_tax_id4 = fields.Float(string='Tax')
    rack_qty = fields.Float(string="stock", compute='compute_stock_qty')
    rate_amt = fields.Float(string="Rate")
    rate_amtc = fields.Float(string="N-rate")
    dis1 = fields.Float('discount 1')
    dis2 = fields.Float('discount 2')
    grand_total = fields.Float('Grand Total')
    calc = fields.Float('Cal', compute="_compute_mass_discount", )
    calc2 = fields.Float('Cal2', )
    calc3 = fields.Float('Cal3', )
    new_disc = fields.Float('Dis2(%)', compute="_compute_cus_ex_discount", )
    amt_tax = fields.Float('Tax_amt', compute="_compute_customer_tax")
    amt_w_tax = fields.Float('Total', compute="_compute_customer_tax")
    doctor_name = fields.Many2one('res.partner', 'Doctor Name')
    doctor_name_1 = fields.Char('Doctor Name')
    address_new = fields.Text('Address')
    product_id = fields.Many2one('product.product', 'Medicine')

    price_subtotal = fields.Float(string='Amount', digits=dp.get_precision('Account'),
                                  store=True, readonly=True, compute='_compute_price', inverse='_inverse_compute_price')

    def _inverse_compute_price(self):
        for rec in self:
            if rec.quantity * rec.price_unit > 0:
                discount_amount = (rec.quantity * rec.price_unit) - rec.price_subtotal
                percentage = (discount_amount * 100) / (rec.quantity * rec.price_unit)
                rec.discount = percentage
                rec.new_disc = percentage

    @api.onchange('price_subtotal')
    def onchange_price_subtotal(self):
        for rec in self:
            if rec.quantity * rec.price_unit > 0:
                discount_amount = (rec.quantity * rec.price_unit) - rec.price_subtotal
                percentage = (discount_amount * 100) / (rec.quantity * rec.price_unit)
                rec.discount = percentage
                rec.new_disc = percentage

    # @api.onchange('product_id')

    @api.onchange('product_id')
    def product_id_change_new(self):
        for rec in self:
            if rec.product_id:
                rec.name = rec.product_id.name
            # if rec.invoice_id:
            #     if rec.invoice_id.partner_id.supplier:
            #         self.search([('invoice_id', '=' , )])

    @api.onchange('medicine_grp')
    def medicine_grp_change_new(self):
        for rec in self:
            if rec.invoice_id.type == 'out_invoice':
                domain = []
                if rec.product_id:
                    domain += [('medicine_1', '=', rec.product_id.id)]
                # if rec.expiry_date:
                #     domain += [('expiry_date', '=', result.expiry_date)]
                if rec.product_of:
                    domain += [('company', '=', rec.product_of.id)]
                if rec.medicine_grp:
                    domain += [('medicine_grp1', '=', rec.medicine_grp.id)]
                if rec.medicine_name_packing:
                    domain += [('medicine_name_packing', '=', rec.medicine_name_packing.id)]
                if rec.medicine_name_subcat:
                    domain += [('potency', '=', rec.medicine_name_subcat.id)]
                rec.name = rec.product_id.name
                rack_ids = []
                stock = self.env['entry.stock'].search(domain)
                for rec in stock:
                    rack_ids.append(rec.rack.id)
                print("racks are", rack_ids)

                return {'domain': {'medicine_rack': [('id', '=', rack_ids)]}}

    @api.onchange('medicine_rack')
    def onchange_compute_stock_qty(self):
        for rec in self:
            if rec.invoice_id.type == 'out_invoice':
                if rec.medicine_rack:
                    domain = [('rack', '=', rec.medicine_rack.id)]
                    if rec.product_id:
                        domain += [('medicine_1', '=', rec.product_id.id)]
                    # if rec.expiry_date:
                    #     domain += [('expiry_date', '=', result.expiry_date)]
                    if rec.product_of:
                        domain += [('company', '=', rec.product_of.id)]
                    if rec.medicine_grp:
                        domain += [('medicine_grp1', '=', rec.medicine_grp.id)]
                    if rec.medicine_name_packing:
                        domain += [('medicine_name_packing', '=', rec.medicine_name_packing.id)]
                    if rec.medicine_name_subcat:
                        domain += [('potency', '=', rec.medicine_name_subcat.id)]
                    stock_ids = self.env['entry.stock'].search(domain)
                    rec.rack_qty = sum(stock_ids.mapped('qty'))

    @api.depends('medicine_rack')
    def compute_stock_qty(self):
        for rec in self:
            if rec.invoice_id.type == 'out_invoice':
                if rec.medicine_rack:
                    domain = [('rack', '=', rec.medicine_rack.id)]
                    if rec.product_id:
                        domain += [('medicine_1', '=', rec.product_id.id)]
                    # if rec.expiry_date:
                    #     domain += [('expiry_date', '=', result.expiry_date)]
                    if rec.product_of:
                        domain += [('company', '=', rec.product_of.id)]
                    if rec.medicine_grp:
                        domain += [('medicine_grp1', '=', rec.medicine_grp.id)]
                    if rec.medicine_name_packing:
                        domain += [('medicine_name_packing', '=', rec.medicine_name_packing.id)]
                    if rec.medicine_name_subcat:
                        domain += [('potency', '=', rec.medicine_name_subcat.id)]
                    stock_ids = self.env['entry.stock'].search(domain)
                    rec.rack_qty = sum(stock_ids.mapped('qty'))

    @api.onchange('medicine_name_subcat')
    def onchange_potency_id(self):
        for rec in self:
            medicine_grp = self.env['medpotency.combo'].search([('potency', '=', rec.medicine_name_subcat.id)])
            medicine_grp_ids = self.env['product.medicine.group'].search(
                [('id', '=', medicine_grp.mapped('groups_id').ids)])
            return {'domain': {'medicine_grp': [('id', 'in', medicine_grp_ids.ids)]}}

    ###########    # tax selection-based on group and potency
    @api.onchange('medicine_grp')
    def onchange_group_id(self):
        for rec in self:
            if rec.medicine_grp.id:
                # print("medicine group exist")
                # grp_obj = self.env['product.medicine.group'].search([('med_grp', '=', rec.medicine_grp.med_grp),
                #                                                     ])
                grp_obj = rec.medicine_grp
                if grp_obj:

                    grp_obj_line = grp_obj.potency_med_ids.search([('medicine', '=', rec.product_id.id),
                                                                   ('potency', '=', rec.medicine_name_subcat.id),
                                                                   ('company', '=', rec.product_of.id),
                                                                   ('groups_id', '=', grp_obj.id)
                                                                   ], order='id desc', limit=1)
                    if grp_obj_line:
                        rec.hsn_code = grp_obj_line.hsn
                        rec.invoice_line_tax_id4 = grp_obj_line.tax

                    else:
                        if rec.product_id.id and rec.medicine_name_subcat.id:
                            grp_obj_line = grp_obj.potency_med_ids.search([('medicine', '=', rec.product_id.id),
                                                                           (
                                                                           'potency', '=', rec.medicine_name_subcat.id),
                                                                           ('company', '=', None),
                                                                           ('groups_id', '=', grp_obj.id)
                                                                           ], order='id desc', limit=1)
                            if grp_obj_line:
                                rec.hsn_code = grp_obj_line.hsn
                                rec.invoice_line_tax_id4 = grp_obj_line.tax

                            else:
                                if rec.product_id.id and rec.product_of.id:
                                    grp_obj_line = grp_obj.potency_med_ids.search([('medicine', '=', rec.product_id.id),
                                                                                   ('potency', '=', None),
                                                                                   ('company', '=', rec.product_of.id),
                                                                                   ('groups_id', '=', grp_obj.id)
                                                                                   ], order='id desc', limit=1)
                                    if grp_obj_line:
                                        rec.hsn_code = grp_obj_line.hsn
                                        rec.invoice_line_tax_id4 = grp_obj_line.tax

                                    else:
                                        if rec.medicine_name_subcat.id and rec.product_of.id:
                                            grp_obj_line = grp_obj.potency_med_ids.search([('medicine', '=', None),
                                                                                           ('potency', '=',
                                                                                            rec.medicine_name_subcat.id),
                                                                                           ('company', '=',
                                                                                            rec.product_of.id),
                                                                                           (
                                                                                           'groups_id', '=', grp_obj.id)
                                                                                           ], order='id desc', limit=1)
                                            if grp_obj_line:
                                                rec.hsn_code = grp_obj_line.hsn
                                                rec.invoice_line_tax_id4 = grp_obj_line.tax

                                            else:
                                                if rec.medicine_name_subcat.id:
                                                    grp_obj_line = grp_obj.potency_med_ids.search(
                                                        [('medicine', '=', None),
                                                         ('potency', '=', rec.medicine_name_subcat.id),
                                                         ('company', '=', None),
                                                         ('groups_id', '=', grp_obj.id)
                                                         ], order='id desc', limit=1)
                                                    if grp_obj_line:
                                                        rec.hsn_code = grp_obj_line.hsn
                                                        rec.invoice_line_tax_id4 = grp_obj_line.tax

                                                    else:
                                                        if rec.product_id.id:
                                                            grp_obj_line = grp_obj.potency_med_ids.search(
                                                                [('medicine', '=', rec.product_id.id),
                                                                 ('potency', '=', None),
                                                                 ('company', '=', None),
                                                                 ('groups_id', '=', grp_obj.id)
                                                                 ], order='id desc', limit=1)
                                                            if grp_obj_line:
                                                                rec.hsn_code = grp_obj_line.hsn
                                                                rec.invoice_line_tax_id4 = grp_obj_line.tax

                                                            else:
                                                                if rec.product_of.id:
                                                                    grp_obj_line = grp_obj.potency_med_ids.search(
                                                                        [('medicine', '=', None),
                                                                         ('potency', '=', None),
                                                                         ('company', '=', rec.product_of.id),
                                                                         ('groups_id', '=', grp_obj.id)
                                                                         ], order='id desc', limit=1)
                                                                    if grp_obj_line:
                                                                        rec.hsn_code = grp_obj_line.hsn
                                                                        rec.invoice_line_tax_id4 = grp_obj_line.tax
                                                                    else:
                                                                        rec.hsn_code = None
                                                                        rec.invoice_line_tax_id4 = 0
                else:
                    rec.hsn_code = None
                    rec.invoice_line_tax_id4 = 0

                    # @api.onchange('medicine_grp')

    # def onchange_group_id(self):
    #     for rec in self:
    #         if self.medicine_grp.id:
    #             # print("medicine group exist")
    #             grp_obj = self.env['product.medicine.group'].search([])
    #             flag = 0
    #             for items in grp_obj:
    #                 # print("inside for loop")
    #                 for lines in items.potency_med_ids:
    #                     # print("1")
    #                     if (rec.product_id.id == lines.medicine.id):
    #                         # print("2")
    #
    #                         if (rec.medicine_name_subcat.id == lines.potency.id):
    #                             # print("3")
    #                             if (rec.product_of.id == lines.company.id):
    #                                 # print("4")
    #                                 rec.hsn_code = lines.hsn
    #                                 rec.invoice_line_tax_id4 = lines.tax
    #                                 rec.product_of = lines.company
    #                                 # print("print tax", lines.tax)
    #                                 flag = 1
    #             if flag == 1:
    #                 # print("flag is 0")
    #                 pass
    #             else:
    #                 grp_obj = self.env['tax.combo.new'].browse(rec.medicine_grp.id)
    #                 if grp_obj.hsn and grp_obj.tax_rate:
    #                     # print("exist both")
    #                     self.hsn_code = grp_obj.hsn
    #                     self.invoice_line_tax_id4 = grp_obj.tax_rate

    #################### PRODUCT SEARCH FOR INVOICE LINE

    @api.multi
    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            price_unit = line.price_unit
            template = {
                'name': line.name or '',
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'location_id': line.invoice_id.partner_id.property_stock_supplier.id,
                'location_dest_id': picking.picking_type_id.default_location_dest_id.id,
                'picking_id': picking.id,
                'move_dest_id': False,
                'state': 'draft',
                'company_id': line.invoice_id.company_id.id,
                'price_unit': price_unit,
                'picking_type_id': picking.picking_type_id.id,
                'procurement_id': False,
                'route_ids': 1 and [
                    (6, 0, [x.id for x in self.env['stock.location.route'].search([('id', 'in', (2, 3))])])] or [],
                'warehouse_id': picking.picking_type_id.warehouse_id.id,
            }
            diff_quantity = line.quantity
            tmp = template.copy()
            tmp.update({
                'product_uom_qty': diff_quantity,
            })
            template['product_uom_qty'] = diff_quantity
            done += moves.create(template)
        return done

    def _create_stock_moves_transfer(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            price_unit = line.price_unit
            template = {
                'name': line.name or '',
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'location_id': picking.picking_type_id.default_location_src_id.id,
                'location_dest_id': line.invoice_id.partner_id.property_stock_customer.id,
                'picking_id': picking.id,
                'move_dest_id': False,
                'state': 'draft',
                'company_id': line.invoice_id.company_id.id,
                'price_unit': price_unit,
                'picking_type_id': picking.picking_type_id.id,
                'procurement_id': False,
                'route_ids': 1 and [
                    (6, 0, [x.id for x in self.env['stock.location.route'].search([('id', 'in', (2, 3))])])] or [],
                'warehouse_id': picking.picking_type_id.warehouse_id.id,
            }
            diff_quantity = line.quantity
            tmp = template.copy()
            tmp.update({
                'product_uom_qty': diff_quantity,
            })
            template['product_uom_qty'] = diff_quantity
            done += moves.create(template)
        return done


class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    _rec_name = "number2"
    _order = "number2 desc"

    packing_invoice = fields.Boolean("Packing Slip?")
    hold_invoice = fields.Boolean("Holding Invoice?")
    cus_invoice = fields.Boolean("Customer Invoice?")
    hold_invoice_id = fields.Many2one("account.invoice", domain=[('type', '=', 'out_invoice'), ('hold_invoice', '=', True)])
    partner_id = fields.Many2one('res.partner',default=1)
    cus_inv_number = fields.Char()
    advance_amount = fields.Float('Advance Amount', related="partner_id.advance_amount")
    cus_invoice_id = fields.Many2one("account.invoice", domain=[('type', '=', 'out_invoice'), ('cus_invoice', '=', True)])
    pack_open_cus_invoice_id = fields.Many2one("account.invoice", domain=[('type', '=', 'out_invoice'), ('cus_invoice', '=', True)])
    pack_invoice_id = fields.Many2one("account.invoice", domain=[('type', '=', 'out_invoice'), ('packing_invoice', '=', True)])


    @api.multi
    def previous_invoice(self):
        next_inv = self.env['account.invoice'].search(
            [(('id', '=', self.id - 1))])
        print(next_inv,'next_inv')
        if next_inv:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            redirect_url = "%s/web#id=%d&view_type=form&model=account.invoice&menu_id=331&action=400" % (
                base_url, next_inv)
            return {
                'type': 'ir.actions.act_url',
                'url': redirect_url,
                'target': 'self',
            }
            # return {
            #     'view_mode': 'form',
            #     'res_id': self.id - 1,
            #     'res_model': 'account.invoice',
            #     'view_id': self.env.ref('account.invoice_form').id,
            #     'type': 'ir.actions.act_window',
            #     'context': {'type': 'out_invoice'},
            #     'target': 'current',
            #     'clear': 1,
            # }
        else:
            raise Warning("Create a new record")


    @api.multi
    def next_invoice(self):
        next_inv = self.env['account.invoice'].search(
            [(('id', '=', self.id + 1))])
        if next_inv:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            redirect_url = "%s/web#id=%d&view_type=form&model=account.invoice&menu_id=331&action=400" % (
                base_url, next_inv)
            return {
                'type': 'ir.actions.act_url',
                'url': redirect_url,
                'target': 'self',
            }
            # return {
            #     'view_mode': 'form',
            #     'res_id': self.id + 1,
            #     'res_model': 'account.invoice',
            #     'view_id': self.env.ref('account.invoice_form').id,
            #     'type': 'ir.actions.act_window',
            #     'context': {'type': 'out_invoice'},
            #     'target': 'current',
            #     'clear': 1,
            # }
        else:
            raise Warning("Create a new record")

    @api.multi
    def open_customer_invoice(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        redirect_url = "%s/web#id=%d&view_type=form&model=account.invoice&menu_id=331&action=400" % (
            base_url, self.cus_invoice_id.id)
        print(redirect_url,'.......>')
        return {
            'type': 'ir.actions.act_url',
            'url': redirect_url,
            'target': 'self',
        }


    @api.multi
    def onchange_cus_invoice_id(self):
        if self.cus_invoice_id:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            redirect_url = "%s/web#id=%d&view_type=form&model=account.invoice&menu_id=331&action=400" % (
                base_url, self.cus_invoice_id.id)
            print(redirect_url,'customer........>')
            return {
                'type': 'ir.actions.act_url',
                'url': redirect_url,
                'target': 'self',
            }
        else:
            pass
        # return {
        #     'view_mode': 'form',
        #     'res_id': self.cus_invoice_id.id,
        #     'res_model': 'account.invoice',
        #     'view_id': self.env.ref('account.invoice_form').id,
        #     'type': 'ir.actions.act_window',
        #     'context': {'type': 'out_invoice'},
        #     'target': 'current',
        #     'clear': 1,
        # }


    @api.multi
    def onchange_pack_cus_invoice_id(self):
        if self.pack_open_cus_invoice_id:
            # hold = self.env['account.invoice'].search([('id','=',self.hold_invoice_id.id),('hold_invoice','=',True),('type','=','out_invoice')])
            # print(hold.hold_invoice,"hold")
            # print(hold.id,"hold.id")
            # print(self.hold_invoice_id.id,"self.hold_invoice_id")
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            redirect_url = "%s/web#id=%d&view_type=form&model=account.invoice&menu_id=331&action=400" % (
                base_url, self.pack_open_cus_invoice_id.id)
            print(redirect_url,'packing........>')
            return {
                'type': 'ir.actions.act_url',
                'url': redirect_url,
                'target': 'self',
            }
        else:
            pass

    @api.multi
    def onchange_hold_invoice_id(self):
        if self.hold_invoice_id:
            # hold = self.env['account.invoice'].search([('id','=',self.hold_invoice_id.id),('hold_invoice','=',True),('type','=','out_invoice')])
            # print(hold.hold_invoice,"hold")
            # print(hold.id,"hold.id")
            # print(self.hold_invoice_id.id,"self.hold_invoice_id")
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            redirect_url = "%s/web#id=%d&view_type=form&model=account.invoice&menu_id=347&action=408" % (
                base_url, self.hold_invoice_id.id)
            return {
                'type': 'ir.actions.act_url',
                'url': redirect_url,
                'target': 'self',
            }
            # return {
            #     'name': _('Holding Invoice'),  # Title of the wizard
            #     'view_mode': 'form',  # Display the wizard in form view
            #     'res_id': self.hold_invoice_id.id,  # ID of the created wizard record
            #     'res_model': 'account.invoice',  # Model of the wizard
            #     'type': 'ir.actions.act_window',
            #     'target': 'self',  # Open the wizard in a new window or tab
            # }
        else:
            pass

    @api.multi
    def onchange_packing_invoice_id(self):
        if self.pack_invoice_id:
            # hold = self.env['account.invoice'].search([('id','=',self.hold_invoice_id.id),('hold_invoice','=',True),('type','=','out_invoice')])
            # print(hold.hold_invoice,"hold")
            # print(hold.id,"hold.id")
            # print(self.hold_invoice_id.id,"self.hold_invoice_id")
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            redirect_url = "%s/web#id=%d&view_type=form&model=account.invoice&menu_id=348&action=409" % (
                base_url, self.pack_invoice_id.id)
            return {
                'type': 'ir.actions.act_url',
                'url': redirect_url,
                'target': 'self',
            }
            # return {
            #     'name': _('Holding Invoice'),  # Title of the wizard
            #     'view_mode': 'form',  # Display the wizard in form view
            #     'res_id': self.hold_invoice_id.id,  # ID of the created wizard record
            #     'res_model': 'account.invoice',  # Model of the wizard
            #     'type': 'ir.actions.act_window',
            #     'target': 'self',  # Open the wizard in a new window or tab
            # }
        else:
            pass

    @api.onchange('financial_year')
    def onchange_pay_mode(self):
        self.date_invoice = date.today()
        if self.type == 'out_invoice' and self.cus_invoice == True:
            res1 = self.env['account.invoice'].search(
                [('type', '=', 'out_invoice'), ('cus_invoice', '=', True)], limit=1)
            number = self.env['ir.sequence'].get('customer.account.invoice')
            self.number2 = number
            self.cus_inv_number = number
            self.seq = 1
            if res1:
                # last_index = int(res1.number2.split('/')[1]) + 1
                # self.number2 = res1.number2.split('/')[0] + "/" + str(last_index).zfill(4)
                # self.cus_inv_number = res1.number2.split('/')[0] + "/" + str(last_index).zfill(4)
                # self.seq = res1.seq + 1
                last_index = int(res1.number2.split('/')[0]) + 1
                print(last_index, 'last_index', res1)
                self.number2 = str(last_index).zfill(4) + "/" + res1.number2.split('/')[1]
                self.cus_inv_number = str(last_index).zfill(4) + "/" + res1.number2.split('/')[1]
                self.seq = res1.seq + 1
            else:
                pass
        if self.type == 'out_invoice' and self.hold_invoice == True:
            res1 = self.env['account.invoice'].search(
                [('type', '=', 'out_invoice'), ('hold_invoice', '=', True)], limit=1)
            number = self.env['ir.sequence'].get('holding.invoice')
            self.number2 = number
            self.cus_inv_number = number
            self.seq = 1
            if res1:
                last_index = int(res1.number2.split('/')[0]) + 1
                print(last_index, 'last_index', res1)
                self.number2 = str(last_index).zfill(4) + "/" + res1.number2.split('/')[1]
                self.cus_inv_number = str(last_index).zfill(4) + "/" + res1.number2.split('/')[1]
                self.seq = res1.seq + 1
            else:
                pass
        if self.type == 'out_invoice' and self.packing_invoice == True:
            res1 = self.env['account.invoice'].search(
                [('type', '=', 'out_invoice'), ('packing_invoice', '=', True)], limit=1)
            number = self.env['ir.sequence'].get('packing.slip.invoice')
            self.number2 = number
            self.cus_inv_number = number
            self.seq = 1
            if res1:
                last_index = int(res1.number2.split('/')[0]) + 1
                print(last_index, 'last_index', res1)
                self.number2 = str(last_index).zfill(4) + "/" + res1.number2.split('/')[1]
                self.cus_inv_number = str(last_index).zfill(4) + "/" + res1.number2.split('/')[1]
                self.seq = res1.seq + 1
            else:
                pass
        if self.type == 'in_invoice':
            res1 = self.env['account.invoice'].search(
                [('type', '=', 'in_invoice')], limit=1)
            number = self.env['ir.sequence'].get('supplier.account.invoice')
            self.number2 = number
            self.seq = 1
            if res1:
                last_index = int(res1.number2.split('/')[0]) + 1
                self.number2 = str(last_index).zfill(4) + "/" + res1.number2.split('/')[1]
                self.cus_inv_number = str(last_index).zfill(4) + "/" + res1.number2.split('/')[1]
                self.seq = res1.seq + 1
            else:
                pass
        # self.number2 = self.env['ir.sequence'].next_by_code('customer.account.invoice')

    @api.multi
    def name_get(self):
        TYPES = {
            'out_invoice': _('Invoice'),
            'in_invoice': _('Supplier Invoice'),
            'out_refund': _('Refund'),
            'in_refund': _('Supplier Refund'),
        }
        result = []
        for inv in self:
            result.append((inv.id, "%s %s" % (TYPES[inv.type], inv.number2 or inv.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('number', '=', name)] + args, limit=limit)
        if not recs:
            recs = self.search([('number2', '=', name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    search_items = fields.Char('.')

    invoices_id = fields.Many2one('account.invoice', 'Select Previous Invoice')
    period_id = fields.Many2one('account.period', 'Select Period')

    @api.multi
    def load(self):
        inv_obj = self.env['account.invoice'].browse(self.invoices_id.id)
        if inv_obj:
            print("yes")
        else:
            print("no")
        for rec in inv_obj:
            new_lines = []
            for line in rec.invoice_line:
                new_lines.append((0, 0, {
                    'name': line.name,
                    'product_id': line.product_id.id,
                    'medicine_name_subcat': line.medicine_name_subcat.id,
                    'medicine_name_packing': line.medicine_name_packing.id,
                    'product_of': line.product_of.id,
                    'medicine_grp': line.medicine_grp.id,
                    'batch_2': line.batch_2.id,
                    'hsn_code': line.hsn_code,
                    'quantity': line.quantity,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'price_subtotal': line.price_subtotal,
                    'invoice_line_tax_id4': line.invoice_line_tax_id4,
                    'amount_amount1': line.amount_amount1,
                    'amount_w_tax': line.amount_w_tax,
                    'manf_date': line.manf_date,
                    'expiry_date': line.expiry_date,
                    'medicine_rack': line.medicine_rack.id,

                }))

        self.write({'invoice_line': new_lines})

    state = fields.Selection([
        ('draft', 'Draft'),
        ('packing_slip', 'Packing Slips'),
        ('holding_invoice', 'Holding Invoice'),
        ('proforma', 'Pro-forma'),
        ('proforma2', 'Pro-forma'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
        ('done', 'Received'),

    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Pro-forma' when invoice is in Pro-forma status,invoice does not have an invoice number.\n"
             " * The 'Open' status is used when user create invoice,a invoice number is generated.Its in open status till user does not pay invoice.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.")

    @api.one
    def add_items(self):
        pass

    number2 = fields.Char()
    # number2 = fields.Char(
    #     'Inv Number', size=16, copy=False,
    #     readonly=True, store=True,
    #     default=lambda self:
    #     self.env['ir.sequence'].next_by_code('customer.account.invoice'))
    duplicate = fields.Boolean()
    seq = fields.Integer()
    holding_invoice = fields.Boolean() #NOT WORKING IN SOME CONDITION USE holding_invoice
    packing_slip = fields.Boolean() #NOT WORKING IN SOME CONDITION  USE packing_slip
    packing_slip_new = fields.Boolean() #NOT WORKING IN SOME CONDITION 

    @api.multi
    def invoice_print(self):
        if self.type == 'out_invoice':
            if self.state == 'open':
                self.state = 'paid'
            if self.state == 'draft':
                self.action_date_assign()
                self.action_move_create()
                self.action_number()
                self.invoice_validate()
        return super(AccountInvoice, self).invoice_print()

    @api.multi
    def print_e_way_report(self):
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }
        data = self.env['ir.actions.report.xml'].search(
            [('model', '=', 'account.invoice'), ('report_name', '=', 'pharmacy_mgmnt.e_way_cus_report_template',)])
        data.download_filename = 'E-way report.pdf'
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'pharmacy_mgmnt.e_way_cus_report_template',
            'file': 'filename',
            'datas': datas,
            'report_type': 'qweb-pdf',
        }



    @api.multi
    def move_to_holding_invoice(self):
        for record in self:
            res = self.env['account.invoice'].search(
                [('type', '=', 'out_invoice'), ('hold_invoice', '=', True)], limit=1)
            last_index = int(res.number2.split('/')[0]) + 1
            record.number2 = str(last_index).zfill(4) + "/" + res.number2.split('/')[1]
            record.cus_inv_number=str(last_index).zfill(4) + "/" + res.number2.split('/')[1]
            record.seq = res.seq + 1
            record.packing_invoice = False
            record.hold_invoice = True
            record.cus_invoice = False
            record.state = "draft"
        return{
            'type': 'ir.actions.client',
            'tag': 'history_back',
        }
        # return {
        #     'name': _('Customer Invoices'),
        #     'view_type': 'tree',
        #     'view_mode': 'tree',
        #     'view_id': self.env.ref('account.invoice_tree').id,
        #     'res_model': 'account.invoice',
        #     'context': "{'type':'out_invoice'}",
        #     'type': 'ir.actions.act_window',
        #     'target': 'main',
        # }


    # @api.multi
    # def move_to_holding_invoice(self):
    #     for record in self:
    #         # if record.state == 'packing_slip':
    #         #     record.state = 'open'
    #         # else:
    #         record.state = 'holding_invoice'
    #         record.holding_invoice = False
    #         record.number2 = self.env['ir.sequence'].next_by_code('holding.invoice')
    #     return

    @api.multi
    def move_to_picking_slip(self):
        for record in self:
            if record.invoice_line:
                record.action_stock_transfer()
            record.packing_slip = True
            record.packing_slip_new = True
            # record.action_date_assign()
            # record.action_move_create()
            # record.action_number()
            # record.invoice_validate()
            record.state = 'packing_slip'

            record.number2 = self.env['ir.sequence'].next_by_code('packing.slip.invoice')

        return

    # @api.multi
    # def move_to_picking_slip(self):
    #     for record in self:
    #         # if record.state == 'packing_slip':
    #         #     record.state = 'open'
    #         # else:
    #         record.state = 'packing_slip'
    #         record.packing_slip = False
    #         record.packing_slip_new = False
    #         record.number2 = self.env['ir.sequence'].next_by_code('packing.slip.invoice')
    #     return

    @api.multi
    def import_to_invoice(self):
        # for record in self:
        #     for line in record.invoice_line:
        #         domain = [('medicine_1','=',line.product_id.name),
        #             ('potency','=',line.medicine_name_subcat.id),
        #             ('medicine_name_packing','=',line.medicine_name_packing.id),
        #             ('company','=',line.product_of.id),
        #             ('medicine_grp1','=',line.medicine_grp.id),
        #             ('mrp','=',line.price_unit),
        #             ('manf_date','=',line.manf_date),
        #             ('expiry_date','=',line.expiry_date),
        #             ('rack','=',line.medicine_rack.id),
        #             ('hsn_code','=',line.hsn_code)]
        #         stock = self.env['entry.stock'].search(domain)
        #         stock.qty_received -= line.quantity
        #         if stock.qty_received < 0:
        #             stock.qty_received = 0
        for record in self:
            res = self.env['account.invoice'].search(
                [('type', '=', 'out_invoice'), ('cus_invoice', '=', True)], limit=1)
            last_index = int(res.number2.split('/')[0]) + 1
            record.number2 = str(last_index).zfill(4) + "/" + res.number2.split('/')[1]
            record.cus_inv_number=str(last_index).zfill(4) + "/" + res.number2.split('/')[1]
            record.seq = res.seq + 1
            record.packing_invoice = False
            record.hold_invoice = False
            record.cus_invoice = True
            record.state = "draft"
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        invoice_id = self.id
        redirect_url = "%s/web#id=%d&view_type=form&model=account.invoice&menu_id=331&action=400" % (
            base_url, invoice_id)
        return {
            'type': 'ir.actions.act_url',
            'url': redirect_url,
            'target': 'self',
        }

    @api.multi
    def invoice_open(self):
        self.ensure_one()
        # Search for record belonging to the current staff
        record = self.env['hiworth.invoice'].search([('origin', '=', self.name)])

        context = self._context.copy()
        context['type2'] = 'out'
        # context['default_name'] = self.id
        if record:
            res_id = record[0].id
        else:
            res_id = False
        # Return action to open the form view
        return {
            'name': 'Invoice view',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_model': 'hiworth.invoice',
            'view_id': 'hiworth_invoice_form',
            'type': 'ir.actions.act_window',
            'res_id': res_id,
            'context': context,
        }

    @api.onchange('invoice_line', 'invoice_line.quantity', 'invoice_line.price_unit', 'invoice_line.discount',
                  'invoice_line.price_subtotal', 'invoice_line.invoice_line_tax_id4')
    def onchange_credit_limit_checking(self):
        for rec in self:
            if rec.partner_id.customer:
                if rec.pay_mode == 'credit':
                    credit_amount = rec.partner_id.limit_amt
                    used = rec.partner_id.used_credit_amt
                    bal = credit_amount - used
                    if (bal <= 0) or (bal < rec.amount_total):
                        raise except_orm(_('Credit Limit Exceeded!'), ('This Customers Credit Limit Amou'
                                                                       'nt Rs. ' + str(
                            credit_amount) + '  has been Crossed.' + "\n" 'Check  ' + rec.partner_id.name + 's' + ' Credit Limits'))

                    if (rec.partner_id.credit_end_date < self.date_invoice):
                        raise except_orm(_('CREDIT DAYS LIMIT REACHED!'), (
                                    'This Customers Credit Limit Days Are Ended' + "\n" 'Please Update the Customer Form'))


    # MY CODE........................................
    @api.model
    def create(self, vals):
        # previous_invoice_number = self.env['account.invoice'].search([], order='seq desc', limit=1).number2.split('/')
        invoice_type = self.env.context.get('default_type') or self._context.get('default_type')
        packing_slip = self.env.context.get('default_packing_invoice') or self._context.get('default_packing_invoice')
        holding_invoice = self.env.context.get('default_hold_invoice') or self._context.get('default_hold_invoice')
        cus_invoice = self.env.context.get('default_cus_invoice') or self._context.get('default_cus_invoice')

        if invoice_type == 'in_invoice':
            res4 = self.env['account.invoice'].search([('type', '=', 'in_invoice')], limit=1)
            number = self.env['ir.sequence'].get('supplier.account.invoice')
            vals['number2'] = number
            vals['cus_inv_number']=number
            vals['seq'] = 1
            if res4:
                last_index = int(res4.number2.split('/')[0]) + 1
                vals['number2'] =  str(last_index).zfill(4)+ "/" +res4.number2.split('/')[1]
                vals['cus_inv_number'] = str(last_index).zfill(4) + "/" + res4.number2.split('/')[1]
                vals['seq'] = res4.seq + 1
            else:
                pass
        if invoice_type == 'out_invoice' and cus_invoice == True:
            res1 = self.env['account.invoice'].search(
                [('type', '=', 'out_invoice'), ('cus_invoice', '=', True)], limit=1)
            number = self.env['ir.sequence'].get('customer.account.invoice')
            vals['number2'] = number
            # print(vals['number2'],'number')
            vals['cus_inv_number'] = number
            vals['seq'] = 1
            if res1:
                last_index = int(res1.number2.split('/')[0]) + 1
                print(last_index,'last_index',res1)
                vals['number2'] = str(last_index).zfill(4) + "/" + res1.number2.split('/')[1]
                vals['cus_inv_number'] = str(last_index).zfill(4) + "/" + res1.number2.split('/')[1]
                vals['seq'] = res1.seq + 1
            else:
                pass
        if packing_slip == True and invoice_type == 'out_invoice':
            res2 = self.env['account.invoice'].search(
                [('type', '=', 'out_invoice'), ('packing_invoice', '=', True), ('hold_invoice', '=', False),], limit=1)
            number = self.env['ir.sequence'].get('packing.slip.invoice')
            vals['number2'] = number
            vals['cus_inv_number'] = number
            vals['seq'] = 1
            if res2:
                last_index = int(res2.number2.split('/')[0]) + 1
                print(last_index, 'last_index', res2)
                vals['number2'] = str(last_index).zfill(4) + "/" + res2.number2.split('/')[1]
                vals['cus_inv_number'] = str(last_index).zfill(4) + "/" + res2.number2.split('/')[1]
                vals['seq'] = res2.seq + 1
            else:
                pass
        if holding_invoice == True and invoice_type == 'out_invoice':
            res3 = self.env['account.invoice'].search(
                [('type', '=', 'out_invoice'), ('hold_invoice', '=', True), ('packing_invoice', '=', False)], limit=1)
            number = self.env['ir.sequence'].get('holding.invoice')
            vals['number2'] = number
            vals['cus_inv_number'] = number
            vals['seq'] = 1
            if res3:
                last_index = int(res3.number2.split('/')[0]) + 1
                print(last_index, 'last_index', res3)
                vals['number2'] = str(last_index).zfill(4) + "/" + res3.number2.split('/')[1]
                vals['cus_inv_number'] = str(last_index).zfill(4) + "/" + res3.number2.split('/')[1]
                vals['seq'] = res3.seq + 1
            else:
                pass
        result = super(AccountInvoice, self).create(vals)
        return result
    #     # ................. OLD CODE..............
    #     # if 'duplicate' in self._context:
    #     #     if self._context['duplicate']:
    #     #         vals.update({'number2': self.browse(self._context['inv_id']).number2, 'duplicate': True})
    #
    #     # result = super(AccountInvoice, self).create(vals)
    #     # if result.type == 'in_invoice' and not result.number2:
    #     #     result.number2 = self.env['ir.sequence'].next_by_code('supplier.account.invoice')
    #     #
    #     # if result.type == 'out_invoice' and not result.number2 and not result.packing_slip and not result.holding_invoice:
    #     #     result.number2 = self.env['ir.sequence'].next_by_code('customer.account.invoice')
    #     #
    #     # if result.packing_slip:
    #     #     result.number2 = self.env['ir.sequence'].next_by_code('packing.slip.invoice')
    #     #     result.state = 'packing_slip'
    #     #     result.packing_slip_new = True
    #     #
    #     # if result.holding_invoice:
    #     #     result.number2 = self.env['ir.sequence'].next_by_code('holding.invoice')
    #     #     result.holding_invoice = True
    #     #     result.state = 'holding_invoice'
    #     # return result
    # endofmycode.............................................
#updated code................................................
    # @api.model
    # def create(self, vals):
    #     invoice_type = self.env.context.get('default_type') or self._context.get('default_type')
    #     packing_slip = self.env.context.get('default_packing_invoice') or self._context.get('default_packing_invoice')
    #     holding_invoice = self.env.context.get('default_hold_invoice') or self._context.get('default_hold_invoice')
    #     cus_invoice = self.env.context.get('default_cus_invoice') or self._context.get('default_cus_invoice')
    #
    #     res = None
    #     number = False
    #
    #     if invoice_type == 'in_invoice':
    #         res = self.env['account.invoice'].search([('type', '=', 'in_invoice')], order='number2 desc', limit=1)
    #         number = self.env['ir.sequence'].get('supplier.account.invoice')
    #     elif cus_invoice:
    #         cus_res = self.env['account.invoice'].search(
    #             [('cus_invoice', '=', True), ('number2', '!=', None)], order='number2 desc', limit=1)
    #         number = self.env['ir.sequence'].get('customer.account.invoice')
    #     elif packing_slip:
    #         res = self.env['account.invoice'].search(
    #             [('type', '=', 'out_invoice'), ('packing_invoice', '=', True)], order='number2 desc', limit=1)
    #         number = self.env['ir.sequence'].get('packing.slip.invoice')
    #     elif holding_invoice:
    #         res = self.env['account.invoice'].search(
    #             [('type', '=', 'out_invoice'), ('hold_invoice', '=', True), ('packing_invoice', '=', False)],
    #             order='number2 desc', limit=1)
    #         number = self.env['ir.sequence'].get('holding.invoice')
    #
    #     if res and res.number2:
    #         last_index = int(res.number2.split('/')[-1])
    #         vals['number2'] = res.number2.split('/')[0] + '/' + str(last_index + 1)
    #         vals['seq'] = res.seq + 1
    #     elif cus_invoice and cus_res and cus_res.number2:
    #         last_index = int(cus_res.number2.split('/')[-1])
    #         vals['number2'] = cus_res.number2.split('/')[0] + '/' + str(last_index + 1)
    #         vals['seq'] = cus_res.seq + 1
    #     else:
    #         vals['number2'] = number
    #         vals['seq'] = 1
    #
    #     result = super(AccountInvoice, self).create(vals)
    #
    #     if cus_invoice and cus_res and cus_res.number2:
    #         next_number = int(cus_res.number2.split('/')[-1]) + 1
    #         sequence = self.env['ir.sequence'].sudo().search([('code', '=', 'customer.account.invoice')], limit=1)
    #         sequence.number_next_actual = next_number
    #
    #     if 'sequence' in locals() and 'next_number' in locals():
    #         sequence.sudo().write({'number_next_actual': next_number})
    #
    #     return result

    # @api.model
    # def create(self, vals):
    #     previous_invoice = self.env['account.invoice'].search([], order='seq desc', limit=1)
    #     previous_invoice_number = previous_invoice.number2.split(
    #         '/') if previous_invoice and previous_invoice.number2 else None
    #     invoice_type = self.env.context.get('default_type') or self._context.get('default_type')
    #     packing_slip = self.env.context.get('default_packing_invoice') or self._context.get('default_packing_invoice')
    #     holding_invoice = self.env.context.get('default_hold_invoice') or self._context.get('default_hold_invoice')
    #     cus_invoice = self.env.context.get('default_cus_invoice') or self._context.get('default_cus_invoice')
    #
    #     res = None  # Default value for 'res'
    #     number = False  # Default value for 'number'
    #
    #     if invoice_type == 'in_invoice':
    #         res = self.env['account.invoice'].search([('type', '=', 'in_invoice')], limit=1)
    #         number = self.env['ir.sequence'].get('supplier.account.invoice')
    #     elif cus_invoice == True:
    #         cus_res = self.env['account.invoice'].search(
    #             [('cus_invoice', '=', True), ('number2', '!=', None)], limit=1)
    #         number = self.env['ir.sequence'].get('customer.account.invoice')
    #         print("number........................", number)
    #         print("number2........................", cus_res.number2)
    #     elif packing_slip == True:
    #         res = self.env['account.invoice'].search(
    #             [('type', '=', 'out_invoice'), ('packing_invoice', '=', True)], limit=1)
    #         number = self.env['ir.sequence'].get('packing.slip.invoice')
    #         print("res packing", res)
    #     elif holding_invoice == True:
    #         print("packing invoice", )
    #         print("packing", packing_slip)
    #         print("holding", holding_invoice)
    #         res = self.env['account.invoice'].search(
    #             [('type', '=', 'out_invoice'), ('hold_invoice', '=', True), ('packing_invoice', '=', False)], limit=1)
    #         print("res holding", res)
    #         number = self.env['ir.sequence'].get('holding.invoice')
    #
    #     if previous_invoice_number is None:
    #         vals['number2'] = number
    #         vals['seq'] = 1
    #     else:
    #         if cus_invoice == True:
    #             if not cus_res:
    #                 vals['number2'] = number
    #                 vals['seq'] = 1
    #             else:
    #                 last_index = int(cus_res.number2.split('/')[-1])
    #                 vals['number2'] = cus_res.number2.split('/')[0] + "/" + str(last_index+1)
    #                 vals['seq'] = cus_res.seq + 1
    #         elif invoice_type == 'in_invoice':
    #             last_index = int(res.number2.split('/')[-1]) + 1
    #             vals['number2'] = res.number2.split('/')[0] + "/" + str(last_index)
    #             vals['seq'] = res.seq + 1
    #         elif packing_slip == True:
    #             vals['number2'] = number
    #             vals['seq'] = 1
    #         elif holding_invoice == True:
    #             if not res:
    #                 vals['number2'] = number
    #                 vals['seq'] = 1
    #             else:
    #                 last_index = int(res.number2.split('/')[-1]) + 1
    #                 vals['number2'] = res.number2.split('/')[0] + "/" + str(last_index)
    #                 vals['seq'] = res.seq + 1
    #
    #     result = super(AccountInvoice, self).create(vals)
    #     return result
    #

    #end...................................................
    #
    @api.multi
    def write(self, vals):
        if 'internal_number' in vals:
            vals['internal_number'] = self.number2
            vals['name'] = self.number2
        return super(AccountInvoice, self).write(vals)

    @api.multi
    def unlink(self):
        for record in self:
            if record.state not in ['draft', 'holding_invoice', 'packing_slip']:
                raise Warning("Only Draft Invoice can be deleted")
        return super(AccountInvoice, self).unlink()

    def copy(self, cr, uid, id, default=None, context=None):
        context.update({'duplicate': True, 'inv_id': id})
        result = super(AccountInvoice, self).copy(cr, uid, id, default, context)
        return result

    @api.multi
    def action_discount1(self):
        return {
            'name': 'group discount',
            'view_type': 'form',
            'view_mode': 'tree',
            'domain': [('inv_id', '=', self.id)],
            'res_model': 'group.discount.copy',
            'type': 'ir.actions.act_window',
            'context': {'current_id': self.id},

        }

    @api.multi
    def action_discount(self):
        prev_rec = self.env['group.discount'].search([])
        if prev_rec:
            for rec in prev_rec:
                rec.unlink()

        return {
            'name': 'group discount',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'group.discount',
            'type': 'ir.actions.act_window',
            'context': {'current_id': self.id},

        }

        # add custom codes here


    #     if self.pay_mode == 'credit':
    #         if self.partner_id.customer:
    #             print("inside credits onchange")

    def get_year(self):
        year = self.env['account.fiscalyear'].search([('state', '=', 'draft')])
        print(year,'yearyear')
        if year:
            return year

    local_customer = fields.Boolean("Local Customer", default=True)
    interstate_customer = fields.Boolean("Interstate Customer")
    b2b = fields.Boolean("B2B")
    b2c = fields.Boolean("B2C", default=True)
    bill_nature = fields.Selection([('gst', 'GST'), ('igst', 'IGST')], default='gst', compute='compute_bill')
    doctor_name = fields.Many2one('res.partner', 'Doctor Name')
    doctor_name_1 = fields.Char('Doctor Name')

    res_person = fields.Many2one('res.partner', string="Responsible Person")
    address_new = fields.Text('Address', related="partner_id.address_new")
    financial_year = fields.Many2one('account.fiscalyear', 'Financial Year', default=get_year)
    inv_sup_no = fields.Char('Invoice No')
    inv_amount = fields.Float('Invoice Amount')

    @api.depends('interstate_customer', 'local_customer')
    def compute_bill(self):
        for rec in self:
            if rec.local_customer:
                rec.bill_nature = 'gst'
            if rec.interstate_customer:
                rec.bill_nature = 'igst'

    @api.multi
    def tree_stock(self):
        print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
        rec = self.env['entry.stock'].sudo.search([])
        print(rec, "alldataaaa222")
        return {
            'name': 'stock tree',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'entry.stock',
            'type': 'ir.actions.act_window',

            'search_view_id': self.env.ref('pharmacy_mgmnt.stock_search_view').id
        }

    @api.multi
    def wiz_tree(self):
        rec = self.env['entry.stock'].sudo.search([])
        print(rec,"alldataaaa11")
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'entry.stock',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def invoice_pay_customer(self, cr, uid, ids, context=None):
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher',
                                                                             'view_vendor_receipt_dialog_form')

        inv = self.browse(cr, uid, ids[0], context=context)
        # if inv.type == "out_invoice":
        #     inv.residual += inv.amount_discount + inv.amount_tax
        return {
            'name': _("Pay Invoice"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.voucher',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'payment_expected_currency': inv.currency_id.id,
                'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(inv.partner_id).id,
                # 'default_amount': inv.type in ('out_refund', 'in_refund') and -residual or residual,
                'default_amount': inv.type in ('out_refund', 'in_refund') and -inv.residual or inv.residual,
                'default_reference': inv.name,
                'close_after_process': True,
                'invoice_type': inv.type,
                'invoice_id': inv.id,
                'default_type': inv.type in ('out_invoice', 'out_refund') and 'receipt' or 'payment',
                'type': inv.type in ('out_invoice', 'out_refund') and 'receipt' or 'payment'
            }
        }

    @api.onchange('residual')
    def onchange_residual(self):
        if self.residual == 0.00:
            print('yes')
            if self._origin.state == 'open':
                print("working...........................................................")
                self.state = 'paid'
                self.update({'state': 'paid'})
        else:
            print("not working")

    # @api.onchange('residual')
    # def onchange_residual(self):
    #     if self.residual == 0.00:
    #         print('yes')
    #         if self.state == 'open':
    #             print("working...........................................................")
    #             self.state = 'paid'
    #             self.write({'state': 'paid'})
    #     else:
    #         print("not working")

    # FOOTER TOTAL AMT CALCULATIONS

    discount_category = fields.Many2one('cus.discount', 'Discount Category', related='partner_id.discount_category')
    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount'), ], default='percent',
                                     string='Discount Type', readonly=True,
                                     states={'draft': [('readonly', False)]}, )
    discount_rate = fields.Float('Discount Rate',
                                 digits_compute=dp.get_precision('Account'),
                                 readonly=True,
                                 states={'draft': [('readonly', False)]}, )
    amount_discount = fields.Float(string='Discount',
                                   digits=dp.get_precision('Account'),
                                   readonly=True, compute='_compute_amount', store=True)
    amount_untaxed = fields.Float(string='Subtotal', digits=dp.get_precision('Account'),
                                  readonly=True, compute='_compute_amount', track_visibility='always')
    amount_tax = fields.Float(string='Tax', digits=dp.get_precision('Account'),
                              readonly=True, compute='_compute_amount', store=True)
    amount_total = fields.Float(string='Total', digits=dp.get_precision('Account'),
                                readonly=True, compute='_compute_amount')
    amount_tax_custom = fields.Float(string='Tax', digits=dp.get_precision('Account'),
                                     store=True, readonly=True, compute='_compute_amount')
    # amount_tax_custom = fields.Float(string='Tax', digits=dp.get_precision('Account'),
    #     store=True, readonly=True, compute='_compute_amount_tax')

    cus_title_1 = fields.Many2one('customer.title', "Customer Type", related="partner_id.cus_title")
    cust_area = fields.Many2one('customer.area', "Customer Area", related="partner_id.cust_area")
    paid_bool = fields.Boolean('Invoice Paid?')
    pay_mode = fields.Selection([('cash', 'Cash'), ('credit', 'Credit'),('upi', 'UPI'),], 'Payment Mode', default='cash')

    amount_in_words = fields.Char('Amount in Words', compute='_compute_amount_in_words')



    @api.depends('amount_total')
    def _compute_amount_in_words(self):
        for invoice in self:
            invoice.amount_in_words = num2words(invoice.amount_total, lang='en').title()

    @api.depends('amount_total')
    def _compute_amount_tax(self):
        for rec in self:
            rec.amount_tax_custom = rec.amount_total - (rec.amount_untaxed - rec.amount_discount)
            rec.amount_tax = rec.amount_tax_custom


    @api.one
    @api.depends('invoice_line.price_subtotal', 'tax_line.amount')
    def _compute_amount(self):
        total_tax_sup = 0.0
        if self.partner_id.supplier:
            amount_untaxed = sum(self.invoice_line.mapped('rate_amt'))
            amount_total_w_tax = sum(self.invoice_line.mapped('amount_w_tax'))
            if amount_total_w_tax <= 0:
                amount_total_w_tax = sum(self.invoice_line.mapped('grand_total'))
            total_price_amount = sum(self.invoice_line.mapped(lambda l: l.quantity * l.price_unit))
            # total_tax_amount = sum(self.invoice_line.mapped('amount_amount1'))
            # total_discount = sum(self.invoice_line.mapped(lambda l: l.dis1 + l.dis2))
            total_tax_amount = amount_total_w_tax - amount_untaxed
            total_discount = total_price_amount - amount_untaxed
            print("total_discounttotal_discounttotal_discount", total_discount)
            # self.rate_amt = self.amount_w_tax - self.amount_amount1
            # discount_2 = 0.0
            # for lines in self.invoice_line:
            #     discount_2 += (lines.quantity * lines.price_unit) * lines.discount3 / 100
                # discount_2 += (lines.quantity * lines.price_unit) * lines.discount3 / 100
            self.amount_untaxed = total_price_amount
            self.amount_tax = total_tax_amount
            self.amount_tax_custom = total_tax_amount
            self.amount_discount = total_discount
            self.amount_total = round(amount_total_w_tax)


        if self.partner_id.customer:
            # print(amount_untaxed,'first')
            amount_untaxed = sum(self.invoice_line.mapped('price_subtotal'))
            print(amount_untaxed,'second')
            amount_total_w_tax = sum(self.invoice_line.mapped('amt_w_tax'))
            print(amount_total_w_tax,'secondsecond')
            if amount_total_w_tax <= 0:
                amount_total_w_tax = sum(self.invoice_line.mapped('grand_total'))
            total_products_tax = sum(self.invoice_line.mapped('product_tax'))
            total_price_amount = sum(self.invoice_line.mapped(lambda l: l.quantity * l.price_unit))
            # total_tax_amount = sum(self.invoice_line.mapped('amt_tax'))
            # total_discount = sum(self.invoice_line.mapped(lambda l: l.dis1 + l.dis2))
            total_tax_amount = abs(amount_total_w_tax - amount_untaxed)
            total_discount = total_price_amount - amount_untaxed
            self.amount_untaxed = total_price_amount
            self.amount_tax = round(total_products_tax)
            self.amount_tax_custom = total_products_tax
            self.amount_discount = total_discount
            self.amount_total = round(amount_total_w_tax)
            self.amount_residual = round(amount_total_w_tax)


    # @api.one
    # @api.depends('invoice_line.price_subtotal', 'tax_line.amount')
    # def _compute_amount(self):
    #     if self.partner_id.supplier == True:
    #         disc = 0.0
    #         total_dis = 0
    #         tax_total = 0
    #         test = 0
    #         test2 =0
    #         test3 =0
    #         for inv in self:
    #             for line in inv.invoice_line:
    #                 print (line.discount)
    #                 disc += (line.quantity * line.price_unit) * line.discount / 100
    #                 test += line.grand_total
    #                 test3 = test3+line.rate_amt
    #                 test2 = test2+(line.quantity * line.price_unit)
    #                 # test2 = test2+line.rate_amt
    #                 total_dis = total_dis +(line.dis1 + line.dis2)
    #                 tax_total = tax_total+line.amount_amount1
    #         self.amount_untaxed = test2
    #         self.amount_tax = tax_total
    #         self.amount_tax_custom = tax_total
    #         total_d = test2 - test3
    #         self.amount_discount = total_d
    #         # self.amount_total = ((test2 -total_d) + tax_total)
    #         self.amount_total = round(test)
    #     if self.partner_id.customer == True:
    #         disc = 0.0
    #         total_dis = 0
    #         tax_total = 0
    #         test = 0
    #         test2 = 0
    #         test3 = 0
    #         for inv in self:
    #             for line in inv.invoice_line:
    #                 print (line.discount)
    #                 disc += (line.quantity * line.price_unit) * line.discount / 100
    #                 test += line.amt_w_tax
    #                 test3 = test3 + line.amt_w_tax
    #                 test2 = test2 + (line.quantity * line.price_unit)
    #                 total_dis = total_dis + (line.dis1 + line.dis2)
    #                 tax_total = tax_total + line.amt_tax
    #         self.amount_untaxed = test2
    #         self.amount_tax = tax_total
    #         total_d = test2 - (test3-tax_total)
    #         self.amount_discount = total_d
    #         # self.amount_total = ((test2 -total_d) + tax_total)
    #         self.amount_total = round(test)

    @api.onchange('discount_category')
    def onchange_category_id(self):
        for rec in self:
            if rec.type != 'in_invoice':
                rec.discount_rate = rec.discount_category.percentage
                for line in rec.invoice_line:
                    line.discount = rec.discount_category.percentage

    @api.depends('discount_category')
    def compute_discount_rate(self):
        for rec in self:
            if rec.type != 'in_invoice':
                rec.discount_rate = rec.discount_category.percentage

    @api.multi
    def compute_discount(self, discount):
        for inv in self:
            val1 = val2 = 0.0
            disc_amnt = 0.0
            val2 = sum(line.amount for line in self.tax_line)
            for line in inv.invoice_line:
                val1 += (line.quantity * line.price_unit)
                line.discount = discount
                disc_amnt += (line.quantity * line.price_unit) * discount / 100
            total = val1 + val2 - disc_amnt
            self.amount_discount = disc_amnt
            # self.amount_tax = val2
            self.amount_total = total

    @api.onchange('discount_type', 'discount_rate')
    def supply_rate(self):
        for inv in self:
            if inv.discount_rate != 0:
                for line in self.invoice_line:
                    line.test3 = inv.discount_rate
                amount = sum(line.price_subtotal for line in self.invoice_line)
                tax = sum(line.amount for line in self.tax_line)
                if inv.discount_type == 'percent':
                    self.compute_discount(inv.discount_rate)
                else:
                    total = 0.0
                    discount = 0.0
                    for line in inv.invoice_line:
                        total += (line.quantity * line.price_unit)
                    if inv.discount_rate != 0:
                        discount = (inv.discount_rate / total) * 100
                    self.compute_discount(discount)

    @api.model
    def _prepare_refund(self, invoice, date=None, period_id=None, description=None, journal_id=None):
        res = super(AccountInvoice, self)._prepare_refund(invoice, date, period_id,
                                                          description, journal_id)
        res.update({
            'discount_type': self.discount_type,
            'discount_rate': self.discount_rate,
        })
        return res

    # UPDATE TAX BUTTON

    @api.multi
    def button_reset_taxes(self):
        res = super(AccountInvoice, self).button_reset_taxes()
        # add custom codes here
        tax_total = 0
        for lines in self.invoice_line:
            if lines.amount_amount1:
                tax_total = tax_total + lines.amount_amount1
        self.amount_tax = tax_total
        self.amount_total = self.amount_total + tax_total
        return res

    ####################### BALANCE CALCULATION###########################################

    def _compute_residual(self):
        for record in self:
            record.residual = 0.0
            # Each partial reconciliation is considered only once for each invoice it appears into,
            # and its residual amount is divided by this number of invoices
            partial_reconciliations_done = []
            for line in record.sudo().move_id.line_id:
                if line.account_id.type not in ('receivable', 'payable'):
                    continue
                if line.reconcile_partial_id and line.reconcile_partial_id.id in partial_reconciliations_done:
                    continue
                # Get the correct line residual amount
                if line.currency_id == record.currency_id:
                    line_amount = line.amount_residual_currency if line.currency_id else line.amount_residual
                else:
                    from_currency = line.company_id.currency_id.with_context(date=line.date)
                    line_amount = from_currency.compute(line.amount_residual, record.currency_id)
                # For partially reconciled lines, split the residual amount
                if line.reconcile_partial_id:
                    partial_reconciliation_invoices = set()
                    for pline in line.reconcile_partial_id.line_partial_ids:
                        if pline.invoice and record.type == pline.invoice.type:
                            partial_reconciliation_invoices.update([pline.invoice.id])
                    line_amount = record.currency_id.round(line_amount / len(partial_reconciliation_invoices))
                    partial_reconciliations_done.append(line.reconcile_partial_id.id)
                record.residual += line_amount
            record.residual = max(record.residual, 0.0)
            # if record.type == "out_invoice" and record.residual != 0:
            #     record.residual += round(record.amount_tax)
            #     record.residual = max(record.residual, 0.0)
            # else:
            #     record.residual = max(record.residual, 0.0)
            if record.state == 'paid':
                record.residual = 0.0



    # def _compute_residual(self):
    #     for record in self:
    #         record.residual = 0.0
    #         partial_reconciliations_done = []
    #         for line in record.sudo().move_id.line_id:
    #             if line.account_id.type not in ('receivable', 'payable'):
    #                 continue
    #             if line.reconcile_partial_id and line.reconcile_partial_id.id in partial_reconciliations_done:
    #                 continue
    #             if line.currency_id == record.currency_id:
    #                 line_amount = line.amount_residual_currency - line.tax_amount if line.currency_id else line.amount_residual - line.tax_amount
    #             else:
    #                 from_currency = line.company_id.currency_id.with_context(date=line.date)
    #                 line_amount = from_currency.compute(line.amount_residual - line.tax_amount, record.currency_id)
    #             if line.reconcile_partial_id:
    #                 partial_reconciliation_invoices = set()
    #                 for pline in line.reconcile_partial_id.line_partial_ids:
    #                     if pline.invoice and record.type == pline.invoice.type:
    #                         partial_reconciliation_invoices.update([pline.invoice.id])
    #                 line_amount = record.currency_id.round(line_amount / len(partial_reconciliation_invoices))
    #                 partial_reconciliations_done.append(line.reconcile_partial_id.id)
    #             record.residual += line_amount
    #         record.residual = max(record.residual, 0.0)
    #         if record.state == 'paid':
    #             record.residual = 0.0

    ########################## INVOICE STOCK MOVE ##############################

    @api.model
    def _default_picking_receive(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)], limit=1)
        if not types:
            types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return types[:1]

    @api.model
    def _default_picking_transfer(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'outgoing'), ('warehouse_id.company_id', '=', company_id)], limit=1)
        if not types:
            types = type_obj.search([('code', '=', 'outgoing'), ('warehouse_id', '=', False)])
        return types[:4]

    picking_count = fields.Integer(string="Count")
    invoice_picking_id = fields.Many2one('stock.picking', string="Picking Id")
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', required=True,
                                      default=_default_picking_receive,
                                      help="This will determine picking type of incoming shipment")
    picking_transfer_id = fields.Many2one('stock.picking.type', 'Deliver To', required=True,
                                          default=_default_picking_transfer,
                                          help="This will determine picking type of outgoing shipment")

    @api.multi
    def action_stock_receive(self):
        for line in self.invoice_line:
            self.env['stock.pick'].create({
                'partner_id': self.partner_id.id,
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'date': self.date_invoice,
                'date_exp': line.expiry_date})

        for order in self:
            if not order.invoice_line:
                pass
                # raise UserError(_('Please create some invoice lines.'))
            if not self.number:
                pass
                # raise UserError(_('Please Validate invoice.'))
            if not self.invoice_picking_id:
                pick = {
                    'picking_type_id': self.picking_type_id.id,
                    'partner_id': self.partner_id.id,
                    'origin': self.number,
                    'location_dest_id': self.picking_type_id.default_location_dest_id.id,
                    'location_id': self.partner_id.property_stock_supplier.id
                }
                picking = self.env['stock.picking'].create(pick)
                self.invoice_picking_id = picking.id
                self.picking_count = len(picking)
                moves = order.invoice_line.filtered(
                    lambda r: r.product_id.type in ['product', 'consu'])._create_stock_moves(picking)
                move_ids = moves.action_confirm()
                move_ids = moves.action_assign()
                move_ids = moves.action_done()

    @api.multi
    def action_stock_transfer(self):
        if not self.packing_slip_new:
            for line in self.invoice_line:
                if not line.stock_transfer_id:
                    stock_transfer_id = self.env['stock.transfer'].create({
                        'partner_id': self.partner_id.id,
                        'title': self.cus_title_1.id,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.quantity,
                        'date': self.date_invoice})
                    line.stock_transfer_id = stock_transfer_id.id

                    domain = [('qty', '>=', line.quantity)]
                    if line.product_id:
                        domain += [('medicine_1', '=', line.product_id.id)]
                    if line.expiry_date:
                        domain += [('expiry_date', '=', line.expiry_date)]
                    if line.medicine_rack:
                        domain += [('rack', '=', line.medicine_rack.id)]
                    if line.product_of:
                        domain += [('company', '=', line.product_of.id)]
                    if line.medicine_grp:
                        domain += [('medicine_grp1', '=', line.medicine_grp.id)]
                    if line.medicine_name_packing:
                        domain += [('medicine_name_packing', '=', line.medicine_name_packing.id)]
                    if line.medicine_name_subcat:
                        domain += [('potency', '=', line.medicine_name_subcat.id)]

                    entry_stock_ids = self.env['entry.stock'].search(domain, order='id asc')
                    if sum(entry_stock_ids.mapped('qty')) <= 0 or not entry_stock_ids:
                        if line.medicine_rack:
                            domain.remove(('rack', '=', line.medicine_rack.id))
                        if line.expiry_date:
                            domain.remove(('expiry_date', '=', line.expiry_date))
                        entry_stock_ids = self.env['entry.stock'].search(domain, order='id asc')
                    if not entry_stock_ids:
                        domain.remove(('qty', '>=', line.quantity))
                        domain += [('qty', '>=', 0)]
                        entry_stock_ids = self.env['entry.stock'].search(domain, order='id asc')

                    if not entry_stock_ids or sum(entry_stock_ids.mapped('qty')) <= 0:
                        raise Warning(
                            _('Only we have %s Products with current combination in stock') % str(
                                int(line.stock_entry_qty) + int(sum(entry_stock_ids.mapped('qty')))))

                    quantity = line.quantity
                    for stock in entry_stock_ids:
                        # if quantity > 0:
                        if stock.qty >= quantity:
                            stock.write({
                                'qty': stock.qty - quantity,
                            })
                            break
                        else:
                            quantity -= stock.qty
                            stock.write({
                                'qty': 0,
                            })

                    line.stock_entry_qty = line.quantity

            for order in self:
                if not order.invoice_line:
                    pass
                    # raise UserError(_('Please create some invoice lines.'))
                if not self.number:
                    pass
                    # raise UserError(_('Please Validate invoice.'))
                if not self.invoice_picking_id:
                    pick = {
                        'picking_type_id': self.picking_transfer_id.id,
                        'partner_id': self.partner_id.id,
                        'origin': self.number,
                        'location_dest_id': self.partner_id.property_stock_customer.id,
                        'location_id': self.picking_transfer_id.default_location_src_id.id
                    }
                    picking = self.env['stock.picking'].create(pick)
                    self.invoice_picking_id = picking.id
                    self.picking_count = len(picking)
                    moves = order.invoice_line.filtered(
                        lambda r: r.product_id.type in ['product', 'consu'])._create_stock_moves_transfer(picking)
                    move_ids = moves.action_confirm()
                    move_ids = moves.action_assign()
                    move_ids = moves.action_done()

    @api.multi
    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree_ready')
        result = action.read()[0]
        result.pop('id', None)
        result['context'] = {}
        result['domain'] = [('id', '=', self.invoice_picking_id.id)]
        pick_ids = sum([self.invoice_picking_id.id])
        if pick_ids:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids or False
        return result

    @api.multi
    def invoice_validate(self):
        if self.type != 'in_invoice' and not self.packing_slip:
            self.action_stock_transfer()
        return self.write({'state': 'open'})


