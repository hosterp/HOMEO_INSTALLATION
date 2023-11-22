from openerp import models, fields, api


class ProductVariantInherit(models.Model):
    _inherit = "product.product"

    # Tax_of_pdt = fields.Char('Medicine Tax')
    Tax_of_pdt = fields.Many2many('account.tax',
                                  'account_invoice_line_tax', 'invoice_line_id', 'tax_id',
                                  string='Taxes',
                                  domain=[('parent_id', '=', False), '|', ('active', '=', False),
                                          ('active', '=', True)])

class Medicines(models.Model):
    _inherit = 'product.template'

    medicine_rack = fields.Many2one('product.medicine.types', 'Medicine Category/Rack')
    product_of = fields.Many2one('product.medicine.responsible', 'Company')
    medicine_name_subcat = fields.Many2one('product.medicine.subcat', 'Potency')
    # medicine_name_subcat = fields.Char('Potency')
    medicine_name_packing = fields.Many2one('product.medicine.packing', 'Packing')
    medicine_grp = fields.Many2one('product.medicine.group', 'Grp')
    # medicine_group = fields.Char('Group')
    batch = fields.Char("Batch")
    tax_ids = fields.Many2many('account.tax', 'name', 'Tax')
    hsn_code = fields.Char('HSN', )
    made_in = fields.Selection([('indian', 'Indian'), ('german', 'German')], default='indian', string="Made In")
    # tax_combo = fields.Many2one('tax.combo', 'Tax')

    @api.constrains('name')
    def _check_name_product(self):
        for record in self:
            old_record = self.search([('name', '=', record.name)])
            if len(old_record.ids)>1:
                raise models.ValidationError('Product Already Created')



    @api.onchange('medicine_name_subcat')
    def onchange_ref_id(self):
        for rec in self:
            pass

    # Tax_of_pdt = fields.Char('Medicine Tax')
    Tax_of_pdt = fields.Many2many('account.tax',
                                  'account_invoice_line_tax', 'invoice_line_id', 'tax_id',
                                  string='Taxes',
                                  domain=[('parent_id', '=', False), '|', ('active', '=', False),
                                          ('active', '=', True)])

