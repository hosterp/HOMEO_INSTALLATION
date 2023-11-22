from openerp import models, fields, api, tools, _
from datetime import datetime, timedelta

class Batches(models.Model):
    _name = "med.batch"
    _rec_name = 'batch'

    batch = fields.Char('Batch')

    @api.constrains('batch')
    def _check_batch(self):
        for record in self:
            old_record = self.search([('batch', '=', record.batch)])
            if len(old_record.ids) > 1:
                raise models.ValidationError('Already Created records for the same Group')

    # _sql_constraints = [
    #     ('batch_name_uniq', 'unique(batch)', 'The name of batch must be unique !'),
    # ]


class MedicineRackSubcat(models.Model):
    _name = 'product.medicine.subcat'
    _rec_name = 'medicine_rack_subcat'

    medicine_rack_subcat = fields.Char(string="Potency Description")

    @api.constrains('medicine_rack_subcat')
    def _check_medicine_rack_subcat(self):
        for record in self:
            old_record = self.search([('medicine_rack_subcat', '=', record.medicine_rack_subcat)])
            if len(old_record.ids) > 1:
                raise models.ValidationError('Potency Already Created')

    # _sql_constraints = [
    #     ('potency_name_uniq', 'unique(medicine_rack_subcat)', 'The Potency name must be unique !'),
    # ]


# TAX-MED-POTENCY-COMBO-RELATION**********************************************************************

class MedPotencyCombo(models.Model):
    _name = 'medpotency.combo'

    groups_id = fields.Many2one('product.medicine.group', string="Group ID")
    medicine = fields.Many2one('product.product', string="Product")
    potency = fields.Many2one('product.medicine.subcat', string='Potency', requiered=True,
                              change_default=True, )
    hsn = fields.Char(string='HSN')
    company = fields.Many2one('product.medicine.responsible', string="Company")
    tax = fields.Float(string='Tax')


class MedicineGroup(models.Model):
    _name = 'product.medicine.group'
    _rec_name = 'med_grp'

    med_grp = fields.Char("Group")
    potency_med_ids = fields.One2many(
        comodel_name='medpotency.combo',
        inverse_name='groups_id',
        string='Potency-Product Link',
        store=True,
    )

    @api.constrains('med_grp')
    def _check_medicine_med_grp(self):
        for record in self:
            old_record = self.search([('med_grp', '=', record.med_grp)])
            if len(old_record.ids) > 1:
                raise models.ValidationError('Group name Already Created')

    # _sql_constraints = [
    #     ('med_grp_name_uniq', 'unique(med_grp)', 'The name of Group must be unique !'),
    # ]


# **********************************************************************************************************

class MedicineTypes(models.Model):
    _name = 'product.medicine.types'
    _rec_name = 'medicine_type'

    medicine_type = fields.Char(string="Position/Rack")
    rack_space = fields.Integer(string="Rack Space")

    # _sql_constraints = [
    #     ('medicine_type_name_uniq', 'unique(medicine_type)', 'The name of Position/Rack must be unique !'),
    # ]

    @api.constrains('medicine_type')
    def _check_medicine_medicine_type(self):
        for record in self:
            old_record = self.search([('medicine_type', '=', record.medicine_type)])
            if len(old_record.ids) > 1:
                raise models.ValidationError('Group name Already Created')


class MedicinePacking(models.Model):
    _name = 'product.medicine.packing'
    _rec_name = 'medicine_pack'

    medicine_pack = fields.Char(string="Packing", unique=True)

    @api.constrains('medicine_pack')
    def _check_medicine_pack(self):
        for record in self:
            old_record = self.search([('medicine_pack', '=', record.medicine_pack)])
            if len(old_record.ids) > 1:
                raise models.ValidationError('Packing name Already Created')

    # _sql_constraints = [
    #     ('medicine_pack_name_uniq', 'unique(medicine_pack)', 'The name of Packing already exists !'),
    # ]


class MedicineResponsible(models.Model):
    _name = 'product.medicine.responsible'
    _rec_name = 'name_responsible'

    name_responsible = fields.Char(string="Product Of ")

    @api.constrains('name_responsible')
    def _check_name_responsible(self):
        for record in self:
            old_record = self.search([('name_responsible', '=', record.name_responsible)])
            if len(old_record.ids) > 1:
                raise models.ValidationError('Company Name Already Created')

    # _sql_constraints = [
    #     ('name_responsible_name_uniq', 'unique(name_responsible)', 'The name of Company must be unique !'),
    # ]


class CustomerDiscounts(models.Model):
    _name = 'cus.discount'
    _rec_name = 'cus_dis'

    cus_dis = fields.Char(string="Discount Category", )
    percentage = fields.Float('Discount In Percentage(%)')

    #
    # _sql_constraints = [
    #     ('cus_dis_name_uniq', 'unique(cus_dis)', 'The name of Discount Category must be unique !'),
    # ]

    @api.constrains('cus_dis')
    def _check_name_cus_dis(self):
        for record in self:
            old_record = self.search([('cus_dis', '=', record.cus_dis)])
            if len(old_record.ids) > 1:
                raise models.ValidationError('Discount Category with same Name Already Created')


# New grp
class TaxComboNew(models.Model):
    _name = 'tax.combo.new'
    _rec_name = 'medicine_grp'

    combo_name = fields.Char('Description')
    medicine_grp = fields.Many2one('product.medicine.group', 'Group')
    product = fields.Many2one('product.template', 'Medicine')
    tax_rate = fields.Float('Tax(%)')
    hsn = fields.Char(string='HSN')
    company = fields.Many2one('product.medicine.responsible', string="Company")
    tax_cat = fields.Selection([('rate_tax', 'RATE TAX'), ('mrp_tax', 'MRP TAX'), ], 'Type', default='rate_tax')
    medicine_name_subcat1 = fields.Many2many(
        comodel_name='product.medicine.subcat',
        inverse_name='medicine_rack_subcat',
        string='Potencies',
        store=True,
    )

    @api.constrains('medicine_grp')
    def _check_name(self):
        for record in self:
            old_record = self.search([('medicine_grp', '=', record.medicine_grp.id)])
            if len(old_record.ids) > 1:
                raise models.ValidationError('Already Created records for the same Group')

    # _sql_constraints = [
    #     ('medicine_grp_name_uniq', 'unique(medicine_grp)', 'The Group must be unique !, Already Created for the Same group'),
    # ]


# class TaxCombo(models.Model):
#     _name = 'tax.combo'
#     _rec_name = 'medicine_grp'
#
#     combo_name = fields.Char('Description')
#     medicine_name_subcat = fields.Many2one('product.medicine.subcat', 'Potency')
#     # medicine_name_subcat1 = fields.Many2many('product.medicine.subcat', 'Potency')
#     medicine_grp = fields.Many2one('product.medicine.group', 'Group')
#     product = fields.Many2one('product.template', 'Medicine')
#     tax_rate = fields.Float('Tax(%)')
#     hsn = fields.Char(string='HSN')
#     company = fields.Many2one('product.medicine.responsible', string="Company")
#     tax_cat = fields.Selection([('rate_tax', 'RATE TAX'), ('mrp_tax', 'MRP TAX'), ], 'Type', default='rate_tax')


# class FindRackMed(models.Model):
#     _name = 'med.rack'
#     _rec_name = 'rack'
#
#     medicine = fields.Many2one('product.template', string="Medicine")
#     medicine_1 = fields.Many2one('product.product', string="Medicine")
#     rack = fields.Many2one('product.medicine.types', 'Rack')
#     qty = fields.Float('Stock Qty in Rack')
#     # racks = fields.One2many(
#     #     comodel_name='rack.batch',
#     #     inverse_name='racks_id',
#     #     string='Medicines',
#     #     store=True,
#     # )
#     racks = fields.One2many(
#         comodel_name='stock.production.lot',
#         inverse_name='racks_id',
#         string='Medicines',
#         store=True,
#     )
#
#     @api.onchange('medicine')
#     def do_find_med(self):
#         print("product template id", self.medicine)
#         print("product name", self.medicine.name)
#         # med_obj = self.env['product.'].search([('product_id','=',self.medicine.id)])
#         self.rack = self.medicine.medicine_rack
#         self.qty = self.medicine.qty_available
#
# class MeDRacks(models.Model):
#     _name = 'rack.batch'
#
#     medicine = fields.Many2one('product.template', string="Medicine")
#     medicine_1 = fields.Many2one('product.product', string="Medicine")
#     potency = fields.Many2one('product.medicine.subcat', 'Potency', )
#     batch = fields.Char('Batch')
#     batch_2 = fields.Many2one('med.batch', "Batch")
#     rack = fields.Many2one('product.medicine.types', 'Rack')
#     qty = fields.Float('Stock')
#     racks_id = fields.Many2one('med.rack', string='Racks')
#     company = fields.Many2one('product.medicine.responsible', 'Company')
#     mrp = fields.Float('Mrp')
#     expiry_date = fields.Date(string='EXP')
#
#     manf_date = fields.Date(string='MFD')
#     medicine_name_packing = fields.Many2one('product.medicine.packing', 'Packing', )

################## Stock Updation #######################
class NewStockEntry(models.Model):
    _name = 'entry.stock'
    _rec_name = 's_no'
    _order = 'id desc'

    supplier_id = fields.Many2one("res.partner", domain="[('supplier', '=', True)]")
    expiry_date = fields.Date(string='Expiry Date')
    manf_date = fields.Date(string='Manufacturing Date')
    alert_date = fields.Date(string='Alert Date')
    s_no = fields.Char('Serial Number', readonly=True, required=True, copy=False, default='New')
    potency = fields.Many2one('product.medicine.subcat', 'Potency', )
    batch = fields.Char('Batch')
    batch_2 = fields.Many2one('med.batch', "Batch")
    rack = fields.Many2one('product.medicine.types', 'Rack')
    qty = fields.Float('Stock')
    # racks_id = fields.Many2one('med.rack', string='Racks')
    company = fields.Many2one('product.medicine.responsible', 'Company')
    mrp = fields.Float('Mrp')
    medicine_name_packing = fields.Many2one('product.medicine.packing', 'Packing', )
    medicine_grp = fields.Many2one('product.medicine.group', 'Group')
    # medicine_grp1 = fields.Many2one('tax.combo.new', 'Group')
    medicine_grp1 = fields.Many2one('product.medicine.group', 'Group')
    medicine_1 = fields.Many2one('product.product', string="Medicine")
    hsn_code = fields.Char('HSN(CODE)')
    invoice_line_tax_id4 = fields.Float(string='GST(%)')
    discount = fields.Float(string='Discount')
    price_subtotal = fields.Float(string='Price Subtotal')
    amount_amount = fields.Float()
    qty_received = fields.Float('Hold Qty')
    amount_w_tax = fields.Float()
    custom_qty = fields.Integer()
    invoice_line_id = fields.Many2one('account.invoice.line')
    quantity_selected = fields.Float(string="Item Qty")
    stock_date = fields.Date(string="stock date")
    med_category = fields.Selection([('indian', 'Indian'), ('german', 'German')], default='indian', string="Made In")

    @api.model
    def create(self, vals):
        if vals.get('s_no', 'New') == 'New':
            vals['s_no'] = self.env['ir.sequence'].next_by_code(
                'stock.entry.sequence') or 'New'
        result = super(NewStockEntry, self).create(vals)
        return result

    @api.onchange('quantity_selected')
    def quantity_selected_onchage(self):
        if self.quantity_selected != 0:
            cus_invoice = self.env['account.invoice'].browse(self.env.context.get('active_id'))
            if cus_invoice:
                new_lines = []
                for rec in self:
                    new_lines.append((0, 0, {
                        'name': rec.medicine_1.name,
                        'product_id': rec.medicine_1.id,
                        'medicine_name_subcat': rec.potency.id,
                        'medicine_name_packing': rec.medicine_name_packing.id,
                        'product_of': rec.company.id,
                        'medicine_grp': rec.medicine_grp1.id,
                        'batch_2': rec.batch_2.id,
                        'hsn_code': rec.hsn_code,
                        'price_unit': rec.mrp,
                        'discount': cus_invoice.discount_rate or 0,
                        'manf_date': rec.manf_date,
                        'expiry_date': rec.expiry_date,
                        'medicine_rack': rec.rack.id,
                        'invoice_line_tax_id4': rec.invoice_line_tax_id4,
                        'rack_qty': rec.qty,
                        'quantity': rec.quantity_selected,
                    }))
                    cus_invoice.write({'invoice_line': new_lines})
                if cus_invoice.hold_invoice == True:
                    hold_qty = self.qty_received + self.quantity_selected
                    if hold_qty >= 0:
                        self.qty_received = hold_qty
                    else:
                        self.qty_received = 0
                else:
                    pass
                self.quantity_selected = 0
            else:
                pass


    # self.quantity_selected=0
    @api.multi
    def call_function(self):
        # print("Active id",self.env.context.get('active_id'))
        cus_invoice = self.env['account.invoice'].browse(self.env.context.get('active_id'))
        if cus_invoice:
            new_lines = []
            for rec in self:
                new_lines.append((0, 0, {
                    'name': rec.medicine_1.name,
                    'product_id': rec.medicine_1.id,
                    'medicine_name_subcat': rec.potency.id,
                    'medicine_name_packing': rec.medicine_name_packing.id,
                    'product_of': rec.company.id,
                    'medicine_grp': rec.medicine_grp1.id,
                    'batch_2': rec.batch_2.id,
                    'hsn_code': rec.hsn_code,
                    'price_unit': rec.mrp,
                    'discount': cus_invoice.discount_rate or 0,
                    'manf_date': rec.manf_date,
                    'expiry_date': rec.expiry_date,
                    'medicine_rack': rec.rack.id,
                    'invoice_line_tax_id4': rec.invoice_line_tax_id4,
                    'rack_qty': rec.qty,

                }))
            cus_invoice.write({'invoice_line': new_lines})
        else:
            pass

    expiry_alert_date = fields.Date(compute='_compute_expiry_alert_date', string='Expiry Alert Date', store=True)

    @api.depends('expiry_date')
    def _compute_expiry_alert_date(self):
        for record in self:
            if record.expiry_date:
                expiry_date = datetime.strptime(record.expiry_date, '%Y-%m-%d').date()
                record.expiry_alert_date = expiry_date - timedelta(days=180)
                print('hi', record.expiry_alert_date)
                # print('hi')
            else:
                record.expiry_alert_date = False


