from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SchoolTeacher(models.Model):
    _name = "school.teacher"
    _description = "Teacher"

    name = fields.Char(string="Full Name", required=True)
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    subject_ids = fields.Many2many("school.subject", string="Subjects")
    hire_date = fields.Date(string="Hire Date")
    active = fields.Boolean(default=True)

    partner_id = fields.Many2one(
        'res.partner',
        string='Teacher Partner',
        ondelete='restrict',
        help="Related partner for invoicing. Auto-created if not set."
    )

    user_id = fields.Many2one(
        'res.users',
        string='Portal User',
        readonly=True,
        help="Automatically created user account for teacher login."
    )

    # -----------------------
    # Create Partner + Portal User Automatically
    # -----------------------
    @api.model_create_multi
    def create(self, vals_list):
        User = self.env['res.users'].sudo()
        Partner = self.env['res.partner'].sudo()
        group_portal = self.env.ref('base.group_portal', raise_if_not_found=False)

        for vals in vals_list:
            # Create partner if missing
            partner = False
            if not vals.get('partner_id') and vals.get('name'):
                partner = Partner.create({
                    'name': vals['name'],
                    'is_company': False,
                })
                vals['partner_id'] = partner.id
            else:
                partner = Partner.browse(vals['partner_id'])

            # Create user (portal)
            if vals.get('name'):
                login_name = vals['name'].replace(" ", "").lower()
                # Avoid duplicates
                if User.search([('login', '=', login_name)]):
                    raise UserError(_("A user with login '%s' already exists.") % login_name)

                new_user = User.create({
                    'name': vals['name'],
                    'login': login_name,
                    'password': '1',
                    'partner_id': partner.id,
                    'groups_id': [(6, 0, [group_portal.id])] if group_portal else False,
                })
                vals['user_id'] = new_user.id

        return super().create(vals_list)

    # -----------------------
    # Sync partner name if teacher name changes
    # -----------------------
    def write(self, vals):
        if 'name' in vals:
            for rec in self:
                if rec.partner_id and not rec.partner_id.is_company:
                    rec.partner_id.name = vals['name']
                if rec.user_id:
                    rec.user_id.name = vals['name']
                    rec.user_id.login = vals['name'].replace(" ", "").lower()
        return super().write(vals)
