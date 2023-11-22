# -*- coding: utf-8 -*-
# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
from datetime import datetime

from dateutil.relativedelta import relativedelta


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'
    _rec_name = 'display_name'

    expiry_date = fields.Date(string='Expiry Date')
    manf_date = fields.Date(string='Manufacturing Date')
    alert_date = fields.Date(string='Alert Date')
    display_name = fields.Char(
        compute='compute_display_name_field',
        string='Lot/Serial Number Display', store=True, readonly=True)

    potency = fields.Many2one('product.medicine.subcat', 'Potency', )
    batch = fields.Char('Batch')
    batch_2 = fields.Many2one('med.batch', "Batch")
    rack = fields.Many2one('product.medicine.types', 'Rack')
    qty = fields.Float('Stock')
    # racks_id = fields.Many2one('med.rack', string='Racks')
    company = fields.Many2one('product.medicine.responsible', 'Company')
    mrp = fields.Float('Mrp')
    # expiry_date = fields.Date(string='EXP')
    # manf_date = fields.Date(string='MFD')
    medicine_name_packing = fields.Many2one('product.medicine.packing', 'Packing', )
    # racks_id = fields.Many2one('med.rack', string='Racks')

    @api.model
    def create(self, vals):
        print("Lot created.............................................")
        result = super(StockProductionLot, self).create(vals)
        if result.expiry_date:

            text = result.expiry_date
            print("value in text",text)

            x = datetime.strptime(text, '%Y-%m-%d')
            print("value in x", x)

            print("alert date cal",x - relativedelta(months=6))
            result.write({
                'alert_date': x - relativedelta(months=6)
            })
        else:
            print("no expiry.......................")

        return result

    # @api.model
    # def write(self, vals):
    #     print("Lot write created.............................................")
    #     result = super(StockProductionLot, self).write(vals)
    #     text = result.expiry_date
    #     print("text",text)
    #     x = datetime.strptime(text, '%Y-%m-%d')
    #     print("x val",x)
    #     print(x - relativedelta(months=6))
    #     if self.expiry_date:
    #         if self.manf_date:
    #             self.write({
    #                 'alert_date': x - relativedelta(months=6)
    #             })
    #     return result

    @api.multi
    @api.depends('name', 'expiry_date')
    def compute_display_name_field(self):
        for lot in self:
            dname = lot.name
            if lot.expiry_date:
                dname = '[%s] %s' % (lot.expiry_date, dname)
            lot.display_name = dname


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    expiry_date = fields.Date(
        related='lot_id.expiry_date', store=True, readonly=True)

    # method copy/pasted from the official product_expiry module
    # © Odoo SA
    @api.model
    def apply_removal_strategy(
            self, location, product, qty, domain, removal_strategy):
        if removal_strategy == 'fefo':
            order = 'expiry_date, location_id, package_id, lot_id, in_date, id'
            return self._quants_get_order(
                location, product, qty, domain, order)
        return super(StockQuant, self).apply_removal_strategy(
            location, product, qty, domain, removal_strategy)
