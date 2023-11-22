from openerp import models, fields, api
from openerp import models, fields, api, tools, _


class CusArea(models.Model):
    _name = 'customer.area'
    _rec_name = 'cus_area'

    cus_area = fields.Char(string="Customer Area")


class CustomerTypes(models.Model):
    _name = 'customer.title'
    _rec_name = 'cus_type'

    cus_type = fields.Char(string="Customer Type")


class ResPartner(models.Model):
    _inherit = "res.partner"
    local_area_customer = fields.Char('Local Area')
    discount_category = fields.Many2one('cus.discount','Discount Category')
    cus_title = fields.Many2one('customer.title', "Customer Type")
    cust_area = fields.Many2one('customer.area', "Customer Area")
    advance_amount=fields.Float('Advance Amount')
    select_state=fields.Selection([('Jammu & Kashmir-01','Jammu & Kashmir-01'),('Himachal Pradesh-02','Himachal Pradesh-02'),('Punjab-03','Punjab-03'),
                                   ('Chandigarh-04', 'Chandigarh-04'),('Uttarakhand-05','Uttarakhand-05'),('Haryana-06','Haryana-06'),
                                   ('Delhi-07', 'Delhi-07'),('Rajasthan-08','Rajasthan-08'),('Uttar Pradesh-09','Uttar Pradesh-09'),
                                   ('Bihar-10', 'Bihar-10'),('Sikkim-11','Sikkim-11'),('Arunachal Pradesh-12','Arunachal Pradesh-12'),
                                   ('Nagaland-13', 'Nagaland-13'),('Manipur-14','Manipur-14'),('Mizoram-15','Mizoram-15'),
                                   ('Tripura-16', 'Tripura-16'),('Meghalaya-17','Meghalaya-17'),('Assam-18','Assam-18'),
                                   ('West Bengal-19', 'West Bengal-19'),('Jharkhand-20','Jharkhand-20'),('Orissa-21','Orissa-21'),
                                   ('Chhattisgarh-22', 'Chhattisgarh-22'),('Madhya Pradesh-23','Madhya Pradesh-23'),('Gujarat-24','Gujarat-24'),
                                   ('Daman & Diu-25', 'Daman & Diu-25'),('Dadra & Nagar Haveli-26','Dadra & Nagar Haveli-26'),('Maharashtra-27','Maharashtra-27'),
                                   ('Andhra Pradesh (Old)-28', 'Andhra Pradesh (Old)-28'),('Andhra Pradesh (New)-37','Andhra Pradesh (New)-37'),('Karnataka-29','Karnataka-29'),
                                   ('Goa-30', 'Goa-30'),('Lakshadweep-31','Lakshadweep-31'),('Kerala-32','Kerala-32'),
                                   ('Tamil Nadu-33', 'Tamil Nadu-33'),('Puducherry-34','Puducherry-34'),('Andaman & Nicobar Islands-35','Andaman & Nicobar Islands-35'),
                                   ('Telengana-36','Telengana-36'),('LADAKH (NEWLY ADDED)-38','LADAKH (NEWLY ADDED)-38'),('OTHER TERRITORY-97','OTHER TERRITORY-97'), ('CENTRE JURISDICTION-99','CENTRE JURISDICTION-99')
                                   ])


    # @api.constrains('name')
    # def _check_name_product(self):
    #     for record in self:
    #         old_record = self.search([('name', '=', record.name)])
    #         if len(old_record.ids) > 1:
    #             raise models.ValidationError('Record Already existing with same name')


    # _sql_constraints = [
    #     ('name_uniq', 'UNIQUE(name)', 'The name of batch must be unique !'),
    # ]

    @api.onchange('b2b')
    def _change_boolean_b2b(self):
        for rec in self:
            if rec.b2b:
                rec.b2c = False
    @api.onchange('b2c')
    def _change_boolean_b2c(self):
        for rec in self:
            if rec.b2c:
                rec.b2b = False
    @api.onchange('interstate_customer')
    def _change_boolean_interstate_customer(self):
        for rec in self:
            if rec.interstate_customer:
                rec.local_customer = False

    @api.onchange('local_customer')
    def _change_boolean_local_customer(self):
        for rec in self:
            if rec.local_customer:
                rec.interstate_customer = False


    # @api.multi
    # @api.depends('gst_no')
    # def _change_boolean_status(self):
    #     for rec in self:
    #         if rec.gst_no:
    #             rec.b2b = True
    #             rec.b2c = False
    #         else:
    #             rec.b2c = True
    #             rec.b2b = False

    local_customer = fields.Boolean()
    interstate_customer = fields.Boolean()
    b2b = fields.Boolean()
    # b2b = fields.Boolean(compute="_change_boolean_status")
    b2c = fields.Boolean()
    gst_no = fields.Char()
    drug_license_number = fields.Char(string='DL/REG NO')
    address_new = fields.Text('Address')
    res_person_id = fields.Boolean('Sale Responsible Person ?')

    @api.onchange('interstate_customer')
    def _default_select_state(self):
        if self.interstate_customer == False:
            default_state = ",Kerala-32"
            self.address_new = default_state
            # print(self.address_new,'address_newaddress_newaddress_newaddress_new')
        else:
            self.address_new=""
            # print(self.address_new,'sdaaaaaaaaaaaaaaafr')
    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        if res.local_area_customer:
            res.name += "," + res.local_area_customer
            print(res.name, ' res.name res.name')
        if vals.get(self.interstate_customer, True):
            # res = super(ResPartner, self).create(vals)
            if 'select_state' in vals:
                select_state = vals['select_state']
                # self._add_address_select_state()
                if select_state == 'Kerala-32':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Jammu & Kashmir-01':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Himachal Pradesh-02':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Punjab-03':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Chandigarh-04':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Uttarakhand-05':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Haryana-06':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Delhi-07':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Rajasthan-08':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Uttar Pradesh-09':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Bihar-10':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Sikkim-11':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Arunachal Pradesh-12':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = self.select_state
                elif select_state == 'Nagaland-13':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Manipur-14':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Mizoram-15':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Tripura-16':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Meghalaya-17':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Assam-18':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'West Bengal-19':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Jharkhand-20':
                    if res.address_new:
                        res.address_new += "," +select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Orissa-21':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Chhattisgarh-22':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Madhya Pradesh-23':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Gujarat-24':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Daman & Diu-25':
                    if res.address_new:
                        res.address_new += "," +select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Dadra & Nagar Haveli-26':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Maharashtra-27':
                    if res.address_new:
                        res.address_new += "," +select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Andhra Pradesh (Old)-28':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Andhra Pradesh (New)-37':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Karnataka-29':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Goa-30':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Lakshadweep-31':
                    if res.address_new:
                        res.address_new += "," +select_state
                    else:
                        res.address_new = select_state

                elif select_state == 'Tamil Nadu-33':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Puducherry-34':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state

                elif select_state == 'Andaman & Nicobar Islands-35':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'Telengana-36':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'LADAKH (NEWLY ADDED)-38':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'OTHER TERRITORY-97':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                elif select_state == 'CENTRE JURISDICTION-99':
                    if res.address_new:
                        res.address_new += "," + select_state
                    else:
                        res.address_new = select_state
                # res.address_new = vals['select_state'] if not res.address_new else res.address_new + ',' + vals[
                #     'select_state']
            print(res, 'res,res')
            return res
        else:
            return None
    @api.onchange('gst_no')
    def b2c_field(self):
        if self.gst_no:
            self.b2b = True
            self.b2c = False
        else:
            self.b2c = True
            self.b2b = False
    @api.multi
    def open_tree_view(self, context=None):
        field_ids = self.env['account.invoice'].search([('res_person', '=', self.id),('packing_slip','=',False),('holding_invoice','=',False)]).ids

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


# GROUPS AND RESTRICTIONS

class ResUsers(models.Model):
    _inherit = 'res.users'

    hide_menu_access_ids = fields.Many2many('ir.ui.menu', 'ir_ui_hide_menu_rel', 'uid', 'menu_id',
                                            string='Hide Access Menu')


class Menu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    @tools.ormcache('frozenset(self.env.user.groups_id.ids)', 'debug')
    def _visible_menu_ids(self, debug=False):
        menus = super(Menu, self)._visible_menu_ids(debug)
        if self.env.user.hide_menu_access_ids and not self.env.user.has_group('base.group_system'):
            for rec in self.env.user.hide_menu_access_ids:
                menus.discard(rec.id)
            return menus
        return menus



