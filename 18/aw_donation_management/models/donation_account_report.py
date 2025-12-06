from odoo import models, fields, api

MONTHS = [
    ('1', 'January'), ('2', 'February'), ('3', 'March'),
    ('4', 'April'), ('5', 'May'), ('6', 'June'),
    ('7', 'July'), ('8', 'August'), ('9', 'September'),
    ('10', 'October'), ('11', 'November'), ('12', 'December'),
]


class DonationAccountReport(models.Model):
    _name = 'donation.account.report'
    _description = 'Donation Account Report'
    _order = 'year desc, month desc, company_id'
    _rec_name = 'display_name'

    company_id = fields.Many2one('res.company', string='Company', required=True)
    month = fields.Selection(MONTHS, string='Month', required=True)
    year = fields.Char(string='Year', required=True)  # Changed to Char to match wizard

    # Donation categories
    zakat = fields.Float(string='Zakat Amount', digits=(16, 2), default=0.0)
    fitrana = fields.Float(string='Fitrana Amount', digits=(16, 2), default=0.0)
    fidya = fields.Float(string='Fidya Amount', digits=(16, 2), default=0.0)
    sadqa = fields.Float(string='Sadqa Amount', digits=(16, 2), default=0.0)
    hadiya_imam_hussain = fields.Float(string='Hadiya Imam Hussain', digits=(16, 2), default=0.0)
    sadqa_mulaqat = fields.Float(string='Sadqa Mulaqat', digits=(16, 2), default=0.0)
    multan_sharif_fund = fields.Float(string='Multan Sharif Fund', digits=(16, 2), default=0.0)
    naat_khaani = fields.Float(string='Naat Khaani', digits=(16, 2), default=0.0)
    hadia = fields.Float(string='Hadia', digits=(16, 2), default=0.0)
    sadqa_shifa = fields.Float(string='Sadqa Shifa', digits=(16, 2), default=0.0)
    special_fund_lahore = fields.Float(string='Special Fund Lahore', digits=(16, 2), default=0.0)
    qurbani_wala_mamla = fields.Float(string='Qurbani Wala Mamla', digits=(16, 2), default=0.0)
    langer_shareef_multan = fields.Float(string='Langer Shareef Multan', digits=(16, 2), default=0.0)
    langer_shareef = fields.Float(string='Langer Shareef', digits=(16, 2), default=0.0)
    syedi_g_ki_neeyat_se_sadqa = fields.Float(string='Syedi G Ki Neeyat Se Sadqa', digits=(16, 2), default=0.0)
    hadia_aqa_ji = fields.Float(string='Hadia Aqa Ji', digits=(16, 2), default=0.0)
    faisal_town_purchase_fund = fields.Float(string='Faisal Town Purchase Fund', digits=(16, 2), default=0.0)
    qurbani_zati = fields.Float(string='Qurbani Zati', digits=(16, 2), default=0.0)
    qurbani_sarkari = fields.Float(string='Qurbani Sarkari', digits=(16, 2), default=0.0)
    hadia_saad_bin_waqas = fields.Float(string='Hadia Saad Bin Waqas', digits=(16, 2), default=0.0)
    hadia_ameer_hamza = fields.Float(string='Hadia Ameer Hamza', digits=(16, 2), default=0.0)

    account_id = fields.Many2one('account.account', string='Account')

    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_total_amount',
        store=True,
        digits=(16, 2)
    )

    # Computed display fields
    month_name = fields.Char(string='Month Name', compute='_compute_display_fields', store=True)
    period = fields.Char(string='Period', compute='_compute_display_fields', store=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_fields', store=True)

    @api.depends(
        'zakat', 'fidya', 'sadqa', 'fitrana', 'hadiya_imam_hussain',
        'sadqa_mulaqat', 'multan_sharif_fund', 'naat_khaani', 'qurbani_wala_mamla',
        'hadia', 'sadqa_shifa', 'special_fund_lahore', 'langer_shareef_multan',
        'langer_shareef', 'syedi_g_ki_neeyat_se_sadqa', 'hadia_aqa_ji',
        'faisal_town_purchase_fund', 'qurbani_zati', 'qurbani_sarkari',
        'hadia_saad_bin_waqas', 'hadia_ameer_hamza'
    )
    def _compute_total_amount(self):
        """Calculate total amount from all categories"""
        for record in self:
            record.total_amount = sum([
                record.zakat, record.fidya, record.sadqa, record.fitrana,
                record.hadiya_imam_hussain, record.sadqa_mulaqat,
                record.multan_sharif_fund, record.naat_khaani,
                record.qurbani_wala_mamla, record.hadia, record.sadqa_shifa,
                record.special_fund_lahore, record.langer_shareef_multan,
                record.langer_shareef, record.syedi_g_ki_neeyat_se_sadqa,
                record.hadia_aqa_ji, record.faisal_town_purchase_fund,
                record.qurbani_zati, record.qurbani_sarkari,
                record.hadia_saad_bin_waqas, record.hadia_ameer_hamza
            ])

    @api.depends('month', 'year', 'company_id')
    def _compute_display_fields(self):
        """Compute month_name, period, and display_name"""
        for record in self:
            record.month_name = dict(MONTHS).get(record.month, '') if record.month else ''
            record.period = f"{record.month_name} {record.year}" if record.month_name and record.year else ''
            company_name = record.company_id.name if record.company_id else ''
            record.display_name = f"{company_name} - {record.period}" if company_name and record.period else 'Donation Report'

    def name_get(self):
        """Custom name display"""
        return [(record.id, record.display_name or 'Donation Report') for record in self]

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        """Override search_read to add company-specific totals only"""
        records = super().search_read(domain, fields, offset, limit, order)
        
        # Only add total row if we have records and a specific context flag
        if records and self.env.context.get('show_totals', False):
            # Check if domain filters by specific company
            company_filter = None
            if domain:
                for condition in domain:
                    if isinstance(condition, (list, tuple)) and len(condition) >= 3:
                        if condition[0] == 'company_id' and condition[1] == '=':
                            company_filter = condition[2]
                            break
            
            # Only show totals if filtering by specific company or if explicitly requested
            if company_filter or self.env.context.get('force_show_totals', False):
                total_row = {field: 0.0 for field in fields if field in [
                    'zakat','fitrana','fidya','sadqa','hadiya_imam_hussain',
                    'sadqa_mulaqat','multan_sharif_fund','naat_khaani','hadia',
                    'sadqa_shifa','special_fund_lahore','qurbani_wala_mamla',
                    'langer_shareef_multan','langer_shareef','syedi_g_ki_neeyat_se_sadqa',
                    'hadia_aqa_ji','faisal_town_purchase_fund','qurbani_zati',
                    'qurbani_sarkari','hadia_saad_bin_waqas','hadia_ameer_hamza',
                    'total_amount'
                ]}
                
                for rec in records:
                    for key in total_row.keys():
                        total_row[key] += rec.get(key, 0.0)

                # Set display fields for total row
                total_row.update({
                    'id': False,
                    'company_id': False,
                    'month': False,
                    'year': False,
                    'account_id': False,
                    'display_name': '--- TOTAL ---',
                    'month_name': '',
                    'period': '',
                })
                
                # Add any other fields that might be requested
                for field in fields:
                    if field not in total_row:
                        total_row[field] = False
                
                records.append(total_row)
        
        return records

    def get_company_summary(self, company_id=None, month=None, year=None):
        """Get summary data for specific company and period"""
        domain = []
        if company_id:
            domain.append(('company_id', '=', company_id))
        if month:
            domain.append(('month', '=', month))
        if year:
            domain.append(('year', '=', year))
        
        records = self.search(domain)
        
        if not records:
            return {}
        
        summary = {
            'zakat': sum(records.mapped('zakat')),
            'fidya': sum(records.mapped('fidya')),
            'sadqa': sum(records.mapped('sadqa')),
            'fitrana': sum(records.mapped('fitrana')),
            'hadiya_imam_hussain': sum(records.mapped('hadiya_imam_hussain')),
            'sadqa_mulaqat': sum(records.mapped('sadqa_mulaqat')),
            'multan_sharif_fund': sum(records.mapped('multan_sharif_fund')),
            'naat_khaani': sum(records.mapped('naat_khaani')),
            'qurbani_wala_mamla': sum(records.mapped('qurbani_wala_mamla')),
            'hadia': sum(records.mapped('hadia')),
            'sadqa_shifa': sum(records.mapped('sadqa_shifa')),
            'special_fund_lahore': sum(records.mapped('special_fund_lahore')),
            'langer_shareef_multan': sum(records.mapped('langer_shareef_multan')),
            'langer_shareef': sum(records.mapped('langer_shareef')),
            'syedi_g_ki_neeyat_se_sadqa': sum(records.mapped('syedi_g_ki_neeyat_se_sadqa')),
            'hadia_aqa_ji': sum(records.mapped('hadia_aqa_ji')),
            'faisal_town_purchase_fund': sum(records.mapped('faisal_town_purchase_fund')),
            'qurbani_zati': sum(records.mapped('qurbani_zati')),
            'qurbani_sarkari': sum(records.mapped('qurbani_sarkari')),
            'hadia_saad_bin_waqas': sum(records.mapped('hadia_saad_bin_waqas')),
            'hadia_ameer_hamza': sum(records.mapped('hadia_ameer_hamza')),
            'total_amount': sum(records.mapped('total_amount')),
            'record_count': len(records),
        }
        
        return summary

    @api.model
    def get_period_comparison(self, current_month, current_year, previous_month, previous_year):
        """Compare donation amounts between two periods"""
        current_records = self.search([
            ('month', '=', current_month),
            ('year', '=', current_year)
        ])
        
        previous_records = self.search([
            ('month', '=', previous_month),
            ('year', '=', previous_year)
        ])
        
        current_total = sum(current_records.mapped('total_amount'))
        previous_total = sum(previous_records.mapped('total_amount'))
        
        difference = current_total - previous_total
        percentage_change = ((difference / previous_total) * 100) if previous_total != 0 else 0
        
        return {
            'current_total': current_total,
            'previous_total': previous_total,
            'difference': difference,
            'percentage_change': percentage_change,
        }

    @api.constrains('month', 'year', 'company_id', 'account_id')
    def _check_unique_record(self):
        """Ensure unique combination of month, year, company, and account"""
        for record in self:
            existing = self.search([
                ('month', '=', record.month),
                ('year', '=', record.year),
                ('company_id', '=', record.company_id.id),
                ('account_id', '=', record.account_id.id if record.account_id else False),
                ('id', '!=', record.id)
            ])
            if existing:
                raise models.ValidationError(
                    f"A report already exists for {record.company_id.name} - "
                    f"{dict(MONTHS)[record.month]} {record.year} - "
                    f"Account: {record.account_id.name if record.account_id else 'N/A'}"
                )