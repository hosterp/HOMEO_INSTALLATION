import datetime
from openerp import api, models, fields, _
from openerp.exceptions import Warning
from collections import defaultdict
from datetime import datetime,date


class TaxReportWizard(models.TransientModel):
    _name = 'tax.report.wizard'

    from_date = fields.Date()
    customer = fields.Many2one('res.partner', domain=[('customer', '=', True)])
    product = fields.Many2one('product.product')
    potency = fields.Many2one('product.medicine.subcat')
    to_date = fields.Date()
    group = fields.Many2one('product.medicine.group')
    company = fields.Many2one('product.medicine.responsible')
    packing = fields.Many2one('product.medicine.packing')
    b2c = fields.Boolean()
    b2b = fields.Boolean()
    by_hsn = fields.Boolean()
    b2c_hsn = fields.Boolean()
    type = fields.Selection([('interstate', 'INTERSTATE'), ('local', 'LOCAL')])

    @api.onchange('by_hsn')
    def onchange_by_hsn(self):
        if self.b2c:
            raise Warning(_('Please select any one (by HSN or b2c or b2b)'))

    @api.onchange('b2c')
    def onchange_b2c(self):
        if self.b2c:
            self.by_hsn = False
            self.b2b = False
            self.b2c_hsn = False

    @api.onchange('by_hsn')
    def onchange_by_hsn(self):
        if self.by_hsn:
            self.b2c = False
            self.b2b = False
            self.b2c_hsn = False

    @api.onchange('b2b')
    def onchange_b2b(self):
        if self.b2b:
            self.by_hsn = False
            self.b2c = False
            self.b2c_hsn = False

    @api.onchange('b2c_hsn')
    def onchange_b2c_hsn(self):
        if self.b2c_hsn:
            self.b2c = False
            self.b2b = False
            self.by_hsn = False

    @api.multi
    def view_tax_report(self):
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }
        data = self.env['ir.actions.report.xml'].search(
            [('model', '=', 'tax.report.wizard'), ('report_name', '=', 'pharmacy_mgmnt.tax_report_template',)])
        if data.download_filename:
            data.download_filename = ''
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'pharmacy_mgmnt.tax_report_template',
            'datas': datas,
            'report_type': 'qweb-html',
        }

    @api.model
    def get_tax_invoices(self):
        domain = [('state', '=', 'paid'), ('type', '=', 'out_invoice')]
        if self.from_date:
            domain = [('invoice_id.date_invoice', '>=', self.from_date)]
        if self.to_date:
            domain += [('invoice_id.date_invoice', '<=', self.to_date)]
        if not self.to_date:
            domain += [('invoice_id.date_invoice', '<=', date.today())]
        if self.customer:
            domain += [('invoice_id.partner_id', '=', self.customer.id)]
        if self.product:
            domain += [('product_id', '=', self.product.id)]
        if self.potency:
            domain += [('medicine_name_subcat', '=', self.potency.id)]
        if self.packing:
            domain += [('medicine_name_packing', '=', self.packing.id)]
        if self.company:
            domain += [('product_of', '=', self.company.id)]
        if self.group:
            domain += [('medicine_grp', '=', self.group.id)]
        res = self.env['account.invoice.line'].search(domain)
        return res

    @api.multi
    def print_tax_report(self):
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }
        data = self.env['ir.actions.report.xml'].search(
            [('model', '=', 'tax.report.wizard'), ('report_name', '=', 'pharmacy_mgmnt.tax_report_template',)])
        data.download_filename = 'Tax report.pdf'
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'pharmacy_mgmnt.tax_report_template',
            'datas': datas,
            'report_type': 'qweb-pdf',
            #
        }

    @api.multi
    def print_tax_report_excel(self):
        if self.by_hsn:
            if self.b2c:
                raise Warning(_('Please select any one (by HSN or b2c)'))
            else:
                datas = {
                    'ids': self._ids,
                    'model': self._name,
                    'form': self.read(),
                    'context': self._context,
                }
                data = self.env['ir.actions.report.xml'].search(
                    [('model', '=', 'tax.report.wizard'), ('report_name', '=', 'pharmacy_mgmnt.b2b_hsn_tax_report_template',)])
                data.download_filename = 'B2B BY HSN report.pdf'
                return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'pharmacy_mgmnt.b2b_hsn_tax_report_template',
                    'datas': datas,
                    'report_type': 'qweb-pdf',
                }
        elif self.b2c_hsn:
            datas = {
                'ids': self._ids,
                'model': self._name,
                'form': self.read(),
                'context': self._context,
            }
            data = self.env['ir.actions.report.xml'].search(
                [('model', '=', 'tax.report.wizard'),
                 ('report_name', '=', 'pharmacy_mgmnt.b2c_hsn_tax_report_template',)])
            data.download_filename = 'B2C BY HSN report.pdf'
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'pharmacy_mgmnt.b2c_hsn_tax_report_template',
                'datas': datas,
                'report_type': 'qweb-pdf',
            }


        # excel not working in offline so created PDF for Offline
        # data = {}
        # data['form'] = self.read(['from_date', 'to_date'])
        # return {'type': 'ir.actions.report.xml',
        #         'report_name': 'pharmacy_mgmnt.report_tax_excel.xlsx',
        #         'datas': data
        #         }
        else:
            datas = {
                'ids': self._ids,
                'model': self._name,
                'form': self.read(),
                'context': self._context,
            }
            if self.b2b:
                data = self.env['ir.actions.report.xml'].search(
                    [('model', '=', 'tax.report.wizard'),
                     ('report_name', '=', 'pharmacy_mgmnt.b2b_tax_report_template',)])
                data.download_filename = 'B2B Tax report.pdf'
            elif self.b2c:
                data = self.env['ir.actions.report.xml'].search(
                    [('model', '=', 'tax.report.wizard'),
                     ('report_name', '=', 'pharmacy_mgmnt.b2b_tax_report_template',)])
                data.download_filename = 'B2C Tax report.pdf'
            else:
                data = self.env['ir.actions.report.xml'].search(
                    [('model', '=', 'tax.report.wizard'),
                     ('report_name', '=', 'pharmacy_mgmnt.b2b_tax_report_template',)])
                data.download_filename = 'GST Tax report.pdf'
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'pharmacy_mgmnt.b2b_tax_report_template',
                'datas': datas,
                'report_type': 'qweb-pdf',
            }

    # @api.multi
    # def get_b2c_hsn_tax_invoices(self):
    #     if self.type == 'interstate':
    #         partner_ids = self.env['res.partner'].search([
    #             ('b2c', '=', True),('interstate_customer', '=', True) ])
    #     elif self.type == 'local':
    #         partner_ids = self.env['res.partner'].search([
    #             ('b2c', '=', True), ('interstate_customer', '=', False)])
    #     else:
    #         partner_ids = self.env['res.partner'].search([
    #             ('b2c', '=', True)])
    #     invoice_ids = self.env['account.invoice'].search([
    #         ('date_invoice', '>=', self.from_date),
    #         ('partner_id', 'in', partner_ids.ids),
    #         ('date_invoice', '<=', self.to_date),
    #         ('packing_slip', '=', False),
    #         ('holding_invoice', '=', False),
    #         ('type', '=', 'out_invoice'),
    #         ('state', '=', 'paid')
    #         ])
    #     data_list = []
    #     for invoice in invoice_ids:
    #         main = {}
    #         lists = []
    #         for rec in invoice.invoice_line:
    #             # if not lists:
    #             hsn_code = rec.hsn_code
    #             invoice_line_tax_id4 = rec.invoice_line_tax_id4
    #             if data_list:
    #                 for record in data_list:
    #                     for recs in record['invoice_data'] :
    #                     # if record['invoice_data'][0]['hsn_code'] == hsn_code and record['invoice_data'][0][
    #                     #     'invoice_line_tax_id4'] == invoice_line_tax_id4:
    #                     #     print(record['invoice_data'][0]['hsn_code'])
    #                     #     print(recs['hsn_code'],'JSN_CODE')
    #                     #     print(hsn_code,'hsn_code')
    #                     #     print(type(recs['hsn_code']),'JSN_CODE')
    #                     #     print(type(hsn_code),'hsn_code')
    #                         if recs['hsn_code'] == hsn_code and recs['invoice_line_tax_id4'] == invoice_line_tax_id4:
    #                             recs['quantity'] += rec.quantity
    #                             recs['product_tax'] += rec.product_tax
    #                             recs['amt_w_tax'] += rec.amt_w_tax
    #                             print(recs['quantity'],'quantity')
    #                             print(recs['product_tax'],'product_tax')
    #                             print(recs['amt_w_tax'],'amt_w_tax')
    #                         # else:
    #                         #     print('hai')
    #                         else:
    #                             print('hai')
    #                             main = {
    #                                 'hsn_code': rec.hsn_code,
    #                                 'quantity': rec.quantity,
    #                                 'invoice_line_tax_id4': rec.invoice_line_tax_id4,
    #                                 'product_tax': rec.product_tax,
    #                                 'amt_w_tax': rec.amt_w_tax,
    #                             }
    #                             lists.append(main)
    #                             # print(lists,'list')
    #                             vals = {
    #                                 'invoice_data': lists
    #                             }
    #                             data_list.append(vals)
    #             else:
    #                 main = {
    #                     'hsn_code': rec.hsn_code,
    #                     'quantity': rec.quantity,
    #                     'invoice_line_tax_id4': rec.invoice_line_tax_id4,
    #                     'product_tax': rec.product_tax,
    #                     'amt_w_tax': rec.amt_w_tax,
    #                 }
    #                 lists.append(main)
    #                 vals = {
    #                     'invoice_data': lists
    #                 }
    #                 data_list.append(vals)
    #     print(data_list, 'data_list')

    @api.multi
    def get_b2c_hsn_tax_invoices(self):
        if self.type == 'interstate':
            partner_ids = self.env['res.partner'].search([
                ('b2c', '=', True), ('interstate_customer', '=', True)])
        elif self.type == 'local':
            partner_ids = self.env['res.partner'].search([
                ('b2c', '=', True), ('interstate_customer', '=', False)])
        else:
            partner_ids = self.env['res.partner'].search([
                ('b2c', '=', True)])

        invoice_ids = self.env['account.invoice'].search([
            ('date_invoice', '>=', self.from_date),
            ('partner_id', 'in', partner_ids.ids),
            ('date_invoice', '<=', self.to_date),
            ('packing_slip', '=', False),
            ('holding_invoice', '=', False),
            ('type', '=', 'out_invoice'),
            ('state', '=', 'paid')
        ])
        data_dict = {}
        for invoice in invoice_ids:
            for rec in invoice.invoice_line:
                hsn_code = rec.hsn_code
                invoice_line_tax_id4 = rec.invoice_line_tax_id4
                key = (hsn_code, invoice_line_tax_id4)
                if key in data_dict:
                    data_dict[key]['quantity'] += rec.quantity
                    data_dict[key]['product_tax'] += rec.product_tax
                    data_dict[key]['amt_w_tax'] += rec.amt_w_tax
                else:
                    data_dict[key] = {
                        'hsn_code': hsn_code,
                        'invoice_line_tax_id4': invoice_line_tax_id4,
                        'quantity': rec.quantity,
                        'product_tax': rec.product_tax,
                        'amt_w_tax': rec.amt_w_tax,
                    }
        data_list = [{'invoice_data': [vals]} for vals in data_dict.values()]
        return data_list

    @api.multi
    def get_b2b_hsn_tax_invoices(self):
        if self.type == 'interstate':
            partner_ids = self.env['res.partner'].search([
                ('b2b', '=', True), ('interstate_customer', '=', True)])
        elif self.type == 'local':
            partner_ids = self.env['res.partner'].search([
                ('b2b', '=', True), ('interstate_customer', '=', False)])
        else:
            partner_ids = self.env['res.partner'].search([
                ('b2b', '=', True)])

        invoice_ids = self.env['account.invoice'].search([
            ('date_invoice', '>=', self.from_date),
            ('date_invoice', '<=', self.to_date),
            ('partner_id', 'in', partner_ids.ids),
            ('packing_slip', '=', False),
            ('holding_invoice', '=', False),
            ('type', '=', 'out_invoice'),
            ('state', '=', 'paid')
        ])
        return invoice_ids
    @api.multi
    def get_b2b_tax_invoices(self):
        if self.b2c:
            if self.type == 'interstate':
                partner_ids = self.env['res.partner'].search([
                    ('b2c', '=', True), ('interstate_customer', '=', True)])
            elif self.type == 'local':
                partner_ids = self.env['res.partner'].search([
                    ('b2c', '=', True), ('interstate_customer', '=', False)])
            else:
                partner_ids = self.env['res.partner'].search([
                    ('b2c', '=', True)])
            # partner_ids = self.env['res.partner'].search([
            #     ('b2c', '=', True), ('b2b', '=', False)])

            invoices = self.env['account.invoice'].search(
                [("date_invoice", ">=", self.from_date), ("date_invoice", "<=", self.to_date),
                 ('partner_id.customer', '=', True), ('partner_id', 'in', partner_ids.ids),
                 ('packing_slip', '=', False), ('holding_invoice', '=', False),
                 ('type', '=', 'out_invoice'), ('state', '=', 'paid')])

            merged_data = defaultdict(lambda: {
                'tax_5_sum': 0,
                'tax_12_sum': 0,
                'tax_18_sum': 0,
                'total_amount_sgst_5':0,
                'total_amount_sgst_12':0,
                'total_amount_sgst_18':0,
                'total_amount_cgst_5':0,
                'total_amount_cgst_12':0,
                'total_amount_cgst_18':0,
                'invoice_numbers': [],
            })

            for invoice in invoices:
                date_str = invoice.date_invoice  # Assuming date_invoice is a string
                date = datetime.strptime(date_str, '%Y-%m-%d').date()

                tax_5 = invoice.invoice_line.filtered(lambda l: l.invoice_line_tax_id4 == 5)
                tax_12 = invoice.invoice_line.filtered(lambda l: l.invoice_line_tax_id4 == 12)
                tax_18 = invoice.invoice_line.filtered(lambda l: l.invoice_line_tax_id4 == 18)

                tax_5_sum = sum(tax_5.mapped('amt_w_tax'))
                tax_12_sum = sum(tax_12.mapped('amt_w_tax'))
                tax_18_sum = sum(tax_18.mapped('amt_w_tax'))

                # Accumulate values in the dictionary
                merged_data[date]['invoice_numbers'].append(invoice.number2)
                merged_data[date]['tax_5_sum'] += tax_5_sum
                merged_data[date]['tax_12_sum'] += tax_12_sum
                merged_data[date]['tax_18_sum'] += tax_18_sum

                merged_data[date]['total_amount_sgst_5']+= (tax_5_sum * 0.05) / 2
                merged_data[date]['total_amount_sgst_12'] += (tax_12_sum * 0.12) / 2
                merged_data[date]['total_amount_sgst_18'] += (tax_18_sum * 0.18) / 2

                merged_data[date]['total_amount_cgst_5'] += (tax_5_sum * 0.05) / 2
                merged_data[date]['total_amount_cgst_12']+= (tax_12_sum * 0.12) / 2
                merged_data[date]['total_amount_cgst_18']+= (tax_18_sum * 0.18) / 2

            # Convert the merged data back to a list
            data_list = []
            for date, values in merged_data.items():
                data_list.append({
                    'date': date,
                    'tax_5_sum': values['tax_5_sum'],
                    'tax_12_sum': values['tax_12_sum'],
                    'tax_18_sum': values['tax_18_sum'],
                    'total_amount_sgst_5':values['total_amount_sgst_5'],
                    'total_amount_sgst_12':values['total_amount_sgst_12'],
                    'total_amount_sgst_18':values['total_amount_sgst_18'],
                    'total_amount_cgst_5':values['total_amount_cgst_5'],
                    'total_amount_cgst_12':values['total_amount_cgst_12'],
                    'total_amount_cgst_18':values['total_amount_cgst_18'],
                    'first_invoice_number': values['invoice_numbers'][0] if values['invoice_numbers'] else None,
                    'last_invoice_number': values['invoice_numbers'][-1] if values['invoice_numbers'] else None,
                })
                for entry in data_list:
                    date = entry['date']
                    invoice_numbers = merged_data[date]['invoice_numbers']
                    entry['invoice_numbers'] = invoice_numbers


            return data_list

        elif self.b2b:
            if self.type == 'interstate':
                partner_ids = self.env['res.partner'].search([
                    ('b2b', '=', True), ('interstate_customer', '=', True)])
            elif self.type == 'local':
                partner_ids = self.env['res.partner'].search([
                    ('b2b', '=', True), ('interstate_customer', '=', False)])
            else:
                partner_ids = self.env['res.partner'].search([
                    ('b2b', '=', True)])
            # partner_ids = self.env['res.partner'].search([
            #     ('b2b', '=', True), ('b2c', '=', False)])
            invoices = self.env['account.invoice'].search(
                [("date_invoice", ">=", self.from_date), ("date_invoice", "<=", self.to_date),
                 ('partner_id.customer', '=', True), ('partner_id', 'in', partner_ids.ids),
                 ('packing_slip', '=', False), ('holding_invoice', '=', False),
                 ('type', '=', 'out_invoice'),
                 ('state', '=', 'paid')])
        else:
            if self.type == 'interstate':
                partner_ids = self.env['res.partner'].search([
                    ('interstate_customer', '=', True)])
            elif self.type == 'local':
                partner_ids = self.env['res.partner'].search([
                    ('interstate_customer', '=', False)])
            else:
                partner_ids = self.env['res.partner'].search([])
            invoices = self.env['account.invoice'].search(
                [("date_invoice", ">=", self.from_date), ("date_invoice", "<=", self.to_date),
                 ('partner_id.customer', '=', True), ('partner_id', 'in', partner_ids.ids),
                 ('packing_slip', '=', False), ('holding_invoice', '=', False),
                 ('type', '=', 'out_invoice')])

        data_list = []
        for invoice in invoices:
            tax_5 = invoice.invoice_line.filtered(lambda l: l.invoice_line_tax_id4 == 5)
            tax_12 = invoice.invoice_line.filtered(lambda l: l.invoice_line_tax_id4 == 12)
            tax_18 = invoice.invoice_line.filtered(lambda l: l.invoice_line_tax_id4 == 18)

            tax_5_sum = sum(tax_5.mapped('amt_w_tax'))
            tax_12_sum = sum(tax_12.mapped('amt_w_tax'))
            tax_18_sum = sum(tax_18.mapped('amt_w_tax'))

            total_amount_sgst_5 = (tax_5_sum * 0.05) / 2
            total_amount_sgst_12 = (tax_12_sum * 0.12) / 2
            total_amount_sgst_18 = (tax_18_sum * 0.18) / 2

            total_amount_cgst_5 = (tax_5_sum * 0.05) / 2
            total_amount_cgst_12 = (tax_12_sum * 0.12) / 2
            total_amount_cgst_18 = (tax_18_sum * 0.18) / 2

            vals = {'invoice': invoice,

                    'tax_5_sum': tax_5_sum,
                    'tax_12_sum': tax_12_sum,
                    'tax_18_sum': tax_18_sum,

                    'total_amount_sgst_5': total_amount_sgst_5,
                    'total_amount_sgst_12': total_amount_sgst_12,
                    'total_amount_sgst_18': total_amount_sgst_18,

                    'total_amount_cgst_5': total_amount_cgst_5,
                    'total_amount_cgst_12': total_amount_cgst_12,
                    'total_amount_cgst_18': total_amount_cgst_18}
            data_list.append(vals)
        return data_list