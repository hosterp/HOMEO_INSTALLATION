from openerp import api, models, fields
from openerp.osv import osv

class MedicineEnquiry(models.Model):
    _name = "medicine.enquiry"
    _description = 'Medicine Enquiry'


    name = fields.Many2one("res.partner", string="Customer", domain="[('customer', '=', True)]")
    phone_no = fields.Char(string="Phone Number")
    address = fields.Char(string="Address")
    medicine_ids = fields.One2many("medicine.enquiry.line", "medicine_line_id")
    state = fields.Selection([('draft', 'Draft'), ('order', 'Order'), ('purchased', 'Purchased')]
                             , required=True, default='draft')

    @api.onchange("name")
    def onchange_name(self):
        if self.name:
            self.address = self.name.address_new
            self.phone_no = self.name.mobile

    @api.multi
    def print_enquiry_report(self):
        if self.state == 'draft':
            self.state = 'order'

        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }
        data = self.env['ir.actions.report.xml'].search(
            [('model', '=', 'medicine.enquiry'), ('report_name', '=', 'pharmacy_mgmnt.report_enquiry_template',)])
        data.download_filename = 'Enquiry report.pdf'
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'pharmacy_mgmnt.report_enquiry_template',
            'file': 'filename',
            'datas': datas,
            'report_type': 'qweb-pdf',
        }
    @api.multi
    def purchase_button(self):
        if self.state=='order':
            self.state='purchased'




class MedicineEnquiryLine(models.Model):
    _name = "medicine.enquiry.line"
    _description = 'Medicine Enquiry Line'

    medicine_line_id = fields.Many2one("medicine.enquiry", string="Medicine Entry")
    medicine_id = fields.Many2one("product.product", string="Medicine")
    group_id = fields.Many2one("product.medicine.group", string="Group")
    potency_id = fields.Many2one("product.medicine.subcat", string="Potency")
    packing_id = fields.Many2one("product.medicine.packing", string="Packing")
    qty = fields.Integer(string="Quantity")

