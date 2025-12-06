from odoo import models, fields, api
from datetime import datetime

# ------------------------------
# Month and Year models
# ------------------------------

class DonationMonth(models.Model):
    _name = 'donation.month'
    _description = 'Month'

    name = fields.Char(string='Month Name', required=True)
    value = fields.Integer(string='Month Number', required=True)


class DonationYear(models.Model):
    _name = 'donation.year'
    _description = 'Year'

    name = fields.Integer(string='Year', required=True)


# ------------------------------
# Donation Reports
# ------------------------------

class DonationReports(models.Model):
    _name = 'donation.reports'
    _description = 'Donation Reports'

    company_id = fields.Many2one('res.company', string='Company', required=True)
    account_id = fields.Many2one('account.account', string='Account', required=True)
    sadqa = fields.Float(string='Sadqa', default=0.0)
    zakat = fields.Float(string='Zakat', default=0.0)
    fidya = fields.Float(string='Fidya', default=0.0)
    total_amount = fields.Float(string='Total Amount', default=0.0)
    months = fields.Char(string="Month")
    year = fields.Integer(string="Year")
    region_id = fields.Many2one("donation.region", string="Region")


# ------------------------------
# Donation Report Wizard
# ------------------------------

class DonationReportWizard(models.TransientModel):
    _name = "donation.report.wizard"
    _description = "Donation Report Wizard"

    company_id = fields.Many2one("res.company", string="Company", required=True)
    region_id = fields.Many2one("donation.region", string="Region")
    account_id = fields.Many2one("account.account", string="Donation Account")
    year = fields.Integer(string="Year", required=True, default=lambda self: datetime.now().year)
    month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'),
        ('04', 'April'), ('05', 'May'), ('06', 'June'),
        ('07', 'July'), ('08', 'August'), ('09', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string="Month")

    def action_generate_report(self):
        """Generate donation report based on selected criteria"""
        self.ensure_one()

        domain = [('company_id', '=', self.company_id.id)]
        if self.account_id:
            domain.append(('account_id', '=', self.account_id.id))
        if self.region_id:
            domain.append(('region_id', '=', self.region_id.id))

        lines = self.env['donation.product.line'].search(domain)

        # Filter by year/month
        if self.year or self.month:
            filtered_lines = []
            for line in lines:
                order = getattr(line, 'donation_order_id', False)
                if order:
                    date = getattr(order, 'donation_date', getattr(order, 'create_date', False))
                    if date:
                        if self.year and str(self.year) != str(date.year):
                            continue
                        if self.month and self.month != str(date.month).zfill(2):
                            continue
                    filtered_lines.append(line)
            lines = self.env['donation.product.line'].browse([l.id for l in filtered_lines])

        # Totals
        sadqa = zakat = fidya = 0.0
        for line in lines:
            amount = line.amount or 0.0
            product_name = (line.product_id.name or '').lower()
            if any(k in product_name for k in ['sadqa', 'صدقہ', 'صدقه']):
                sadqa += amount
            elif any(k in product_name for k in ['zakat', 'زکات', 'زکوٰہ']):
                zakat += amount
            elif any(k in product_name for k in ['fidya', 'فدیہ', 'fitrana']):
                fidya += amount

        # Default account if not selected
        account_id = self.account_id.id or self.env['account.account'].search([('company_id', '=', self.company_id.id)], limit=1).id

        result = self.env['donation.reports'].create({
            'company_id': self.company_id.id,
            'account_id': account_id,
            'region_id': self.region_id.id if self.region_id else False,
            'year': self.year,
            'months': self.month or '',
            'sadqa': sadqa,
            'zakat': zakat,
            'fidya': fidya,
            'total_amount': sadqa + zakat + fidya,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Donation Report',
            'res_model': 'donation.reports',
            'view_mode': 'form',
            'res_id': result.id,
            'target': 'current',
        }
