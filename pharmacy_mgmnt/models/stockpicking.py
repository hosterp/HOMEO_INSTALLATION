from openerp import models, fields, api


class StockpickInherit(models.Model):
    _name = 'stock.pick'

    partner_id = fields.Many2one('res.partner', string="Supplier")
    product_id = fields.Many2one('product.product', string="Medicine")
    product_uom_qty = fields.Float(string="Quantity")
    date = fields.Date('Received Date')
    date_exp = fields.Date('Expiry Date')


# MEDICINE TRANSFER

class StockpickInheritSold(models.Model):
    _name = 'stock.transfer'
    _order = 'id desc'

    partner_id = fields.Many2one('res.partner', string="Customer")
    title = fields.Many2one('customer.title','Customer Title')
    product_id = fields.Many2one('product.product', string="Medicine")
    product_uom_qty = fields.Float(string="Quantity")
    date = fields.Date('Date')
