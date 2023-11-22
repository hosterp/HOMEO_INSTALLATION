from openerp import models, fields, api, _
from openerp import tools, _
from datetime import datetime, date, timedelta


class PendingInvoiceReport(models.TransientModel):
    _name = 'pending.invoice.report'

    partner_id = fields.Many2one('res.partner', 'Customer')
    resp_partner_id = fields.Many2one('res.partner', 'Responsible Person')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')

    @api.multi
    def action_pending_invoice_open_window(self):
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }
        data = self.env['ir.actions.report.xml'].search(
            [('model', '=', 'pending.invoice.report'), ('report_name', '=', 'pharmacy_mgmnt.report_pending_invoice_template_new',)])
        data.download_filename = 'customer pending payment report.pdf'
        return {
            'name': 'Pending Invoice Report',
            'type': 'ir.actions.report.xml',
            'report_name': 'pharmacy_mgmnt.report_pending_invoice_template_new',
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
            if self.resp_partner_id:
                cust_invs = self.env['account.invoice'].search(
                    [('date_invoice', '>=', self.date_from), ('date_invoice', '<=', self.date_to),
                     ('partner_id', '=', self.partner_id.id), ('res_person', '=', self.resp_partner_id.id),
                     ('packing_slip','=', False),('holding_invoice', '=', False), ('state', '=', 'open'),
                     ('type', '=', 'out_invoice')])
            else:
                cust_invs = self.env['account.invoice'].search(
                    [('date_invoice', '>=', self.date_from), ('date_invoice', '<=', self.date_to),
                     ('partner_id', '=', self.partner_id.id), ('packing_slip','=',False),('holding_invoice','=',False),
                     ('state', '=', 'open'), ('type', '=', 'out_invoice')])
        else:
            if self.resp_partner_id:
                cust_invs = self.env['account.invoice'].search(
                    [('date_invoice', '>=', self.date_from), ('date_invoice', '<=', self.date_to),
                     ('res_person', '=', self.resp_partner_id.id), ('packing_slip','=',False),
                     ('holding_invoice','=',False), ('state', '=', 'open'),
                     ('type', '=', 'out_invoice')])
            else:
                cust_invs = self.env['account.invoice'].search(
                    [('date_invoice', '>=', self.date_from), ('date_invoice', '<=', self.date_to), ('packing_slip','=',False),('holding_invoice','=',False),
                     ('state', '=', 'open'), ('type', '=', 'out_invoice')])

        for rec in cust_invs:
            if rec.state == 'draft':
                pass
            else:
                paid_amt = (rec.amount_total - rec.residual)

                vals = {

                    'date': rec.date_invoice,
                    'customer': rec.partner_id.name,
                    'res_person': rec.res_person.name,
                    'bill_amt': round(rec.amount_total,2),
                    'paid_amt': round(paid_amt, 2),
                    'bal_amt': round(rec.residual,2),
                    'total_bal':0,
                    'total_paid':0,
                    'total_sub':0,

                }
                lst.append(vals)
        sum = 0
        for vals in lst:
            sum = round(sum + vals['bal_amt'], 2)
        print("balance amt ",sum)
        for vals in lst:
            vals['total_bal'] = sum

        sum1 = 0
        for vals in lst:
            sum1 = round(sum1 + vals['paid_amt'], 2)
        print("paid amt ",sum1)

        for vals in lst:
            vals['total_paid'] = sum1

        sum2 = 0
        for vals in lst:
            sum2 = round(sum2 + vals['bill_amt'], 2)
        print("bill amt ",sum2)

        for vals in lst:
            vals['total_sub'] = sum2

        return lst
