from odoo import models, fields, api
from datetime import datetime

# =====================================================
# ---------------- LIBERIA FAMILY ----------------------
# =====================================================
from odoo import models, fields, api


class LiberiaFamily(models.Model):
    _name = 'liberia.family'
    _description = 'Liberia Family Project'
    _order = 'id desc'
    _rec_name = "name_en"

    # English fields
    name_en = fields.Char("Family Name (EN)")
    age_en = fields.Integer("Age (EN)")
    location_en = fields.Char("Location (EN)")
    project_title_en = fields.Char("Project Title (EN)")
    project_description_en = fields.Text("Project Description (EN)")
    investment_needed_en = fields.Float("Investment Needed (EN) ($)")
    current_income_en = fields.Float("Current Income (EN) ($)")
    additional_income_en = fields.Float("Additional Income (EN) ($)")
    receivew_1_en = fields.Char("Your Benefits as Donor1 (EN)")
    receivew_2_en = fields.Char("Your Benefits as Donor2 (EN) ")
    receivew_3_en = fields.Char("Your Benefits as Donor3 (EN)")
    receivew_4_en = fields.Char("Your Benefits as Donor4 (EN)")
    photo = fields.Binary("Family Photo")
    photo_filename = fields.Char("Photo Filename")
    progress_percentage_en = fields.Float("Progress (%) (EN)")

    # German fields
    name_de = fields.Char("Family Name (DE)")
    age_de = fields.Integer("Age  (DE)")
    location_de = fields.Char("Location  (DE)")
    project_title_de = fields.Char("Project Title  (DE)")
    project_description_de = fields.Text("Project Description  (DE)")
    investment_needed_de = fields.Float("Investment Needed  (DE) ($)")
    current_income_de = fields.Float("Current Income  (DE) ($)")
    additional_income_de = fields.Float("Additional Income  (DE) ($)")
    receivew_1_de = fields.Char("Your Benefits as Donor1  (DE)")
    receivew_2_de = fields.Char("Your Benefits as Donor2  (DE)")
    receivew_3_de = fields.Char("Your Benefits as Donor3  (DE)")
    receivew_4_de = fields.Char("Your Benefits as Donor4  (DE)")
    progress_percentage_de = fields.Float("Progress (%) (DE)")

    # @api.onchange('name')
    # def _onchange_name_upper(self):
    #     if self.name:
    #         self.name = self.name.upper()
    #
    # @api.model
    # def create(self, vals):
    #     if vals.get('name'):
    #         vals['name'] = vals['name'].upper()
    #     return super(LiberiaFamily, self).create(vals)
    #
    # def write(self, vals):
    #     if vals.get('name'):
    #         vals['name'] = vals['name'].upper()
    #     return super(LiberiaFamily, self).write(vals)


# =====================================================
# ---------------- SIERRA FAMILY ----------------------
# =====================================================
class SierraFamily(models.Model):
    _name = 'sierra.family'
    _description = 'Sierra Family Project'
    _order = 'id desc'
    _rec_name = "name_en"

    # English fields
    name_en = fields.Char("Family Name (EN)")
    age_en = fields.Integer("Age (EN)")
    location_en = fields.Char("Location (EN)")
    project_title_en = fields.Char("Project Title (EN)")
    project_description_en = fields.Text("Project Description (EN)")
    investment_needed_en = fields.Float("Investment Needed (EN) ($)")
    current_income_en = fields.Float("Current Income (EN) ($)")
    additional_income_en = fields.Float("Additional Income (EN) ($)")
    receivew_1_en = fields.Char("Your Benefits as Donor1 (EN)")
    receivew_2_en = fields.Char("Your Benefits as Donor2 (EN) ")
    receivew_3_en = fields.Char("Your Benefits as Donor3 (EN)")
    receivew_4_en = fields.Char("Your Benefits as Donor4 (EN)")
    photo = fields.Binary("Family Photo")
    photo_filename = fields.Char("Photo Filename")
    progress_percentage_en = fields.Float("Progress (%) (EN)")

    # German fields
    name_de = fields.Char("Family Name (DE)")
    age_de = fields.Integer("Age  (DE)")
    location_de = fields.Char("Location  (DE)")
    project_title_de = fields.Char("Project Title  (DE)")
    project_description_de = fields.Text("Project Description  (DE)")
    investment_needed_de = fields.Float("Investment Needed  (DE) ($)")
    current_income_de = fields.Float("Current Income  (DE) ($)")
    additional_income_de = fields.Float("Additional Income  (DE) ($)")
    receivew_1_de = fields.Char("Your Benefits as Donor1  (DE)")
    receivew_2_de = fields.Char("Your Benefits as Donor2  (DE)")
    receivew_3_de = fields.Char("Your Benefits as Donor3  (DE)")
    receivew_4_de = fields.Char("Your Benefits as Donor4  (DE)")
    progress_percentage_de = fields.Float("Progress (%) (DE)")

    #
    # @api.onchange('name')
    # def _onchange_name_upper(self):
    #     if self.name:
    #         self.name = self.name.upper()

    # @api.model
    # def create(self, vals):
    #     if vals.get('name'):
    #         vals['name'] = vals['name'].upper()
    #     return super(SierraFamily, self).create(vals)
    #
    # def write(self, vals):
    #     if vals.get('name'):
    #         vals['name'] = vals['name'].upper()
    #     return super(SierraFamily, self).write(vals)


# =====================================================
# ---------------- AFGHANISTAN FAMILY -----------------
# =====================================================
class AfghanistanFamily(models.Model):
    _name = 'afghanistan.family'
    _description = 'Afghanistan Family Project'
    _order = 'id desc'
    _rec_name = "name_en"

    # English fields
    name_en = fields.Char("Family Name (EN)")
    age_en = fields.Integer("Age (EN)")
    location_en = fields.Char("Location (EN)")
    project_title_en = fields.Char("Project Title (EN)")
    project_description_en = fields.Text("Project Description (EN)")
    investment_needed_en = fields.Float("Investment Needed (EN) ($)")
    current_income_en = fields.Float("Current Income (EN) ($)")
    additional_income_en = fields.Float("Additional Income (EN) ($)")
    receivew_1_en = fields.Char("Your Benefits as Donor1 (EN)")
    receivew_2_en = fields.Char("Your Benefits as Donor2 (EN) ")
    receivew_3_en = fields.Char("Your Benefits as Donor3 (EN)")
    receivew_4_en = fields.Char("Your Benefits as Donor4 (EN)")
    photo = fields.Binary("Family Photo")
    photo_filename = fields.Char("Photo Filename")
    progress_percentage_en = fields.Float("Progress (%) (EN)")

    # German fields
    name_de = fields.Char("Family Name (DE)")
    age_de = fields.Integer("Age  (DE)")
    location_de = fields.Char("Location  (DE)")
    project_title_de = fields.Char("Project Title  (DE)")
    project_description_de = fields.Text("Project Description  (DE)")
    investment_needed_de = fields.Float("Investment Needed  (DE) ($)")
    current_income_de = fields.Float("Current Income  (DE) ($)")
    additional_income_de = fields.Float("Additional Income  (DE) ($)")
    receivew_1_de = fields.Char("Your Benefits as Donor1  (DE)")
    receivew_2_de = fields.Char("Your Benefits as Donor2  (DE)")
    receivew_3_de = fields.Char("Your Benefits as Donor3  (DE)")
    receivew_4_de = fields.Char("Your Benefits as Donor4  (DE)")
    progress_percentage_de = fields.Float("Progress (%) (DE)")

    # @api.onchange('name')
    # def _onchange_name_upper(self):
    #     if self.name:
    #         self.name = self.name.upper()

    # @api.model
    # def create(self, vals):
    #     if vals.get('name'):
    #         vals['name'] = vals['name'].upper()
    #     return super(AfghanistanFamily, self).create(vals)
    #
    # def write(self, vals):
    #     if vals.get('name'):
    #         vals['name'] = vals['name'].upper()
    #     return super(AfghanistanFamily, self).write(vals)

    # =====================================================
    # ---------------- COMMUNITY MODELS -------------------
    # =====================================================
    class LiberiaCommunity(models.Model):
        _name = "liberia.community"
        _description = "Liberia Community"
        _rec_name = "name_en"

        # -------------------------
        # English Fields (EN)
        # -------------------------
        month_from_en = fields.Selection([
            ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
            ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
            ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'),
        ], string="From Month (EN)")

        month_to_en = fields.Selection([
            ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
            ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
            ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'),
        ], string="To Month (EN)")

        name_en = fields.Char("Community Name (EN)", required=True)
        plot_project_en = fields.Char("Project Name (EN)")
        location_en = fields.Char("Location (EN)")
        number_beneficiaries_en = fields.Char("Number of Beneficiaries (EN)")
        distribution_en = fields.Text("Project Detail (EN)")
        duration_en = fields.Char("Duration (EN)", compute="_compute_duration_en", store=True)

        budget_en = fields.Char("Budget (EN)")
        beneficiaries_en = fields.Char("Beneficiaries (EN)")
        investment_needed_en = fields.Char("Investment Needed ($) (EN)")
        current_income_en = fields.Char("Current Avg Monthly Income ($) (EN)")
        additional_income_en = fields.Char("Expected Income from Project ($) (EN)")

        receivew_1_en = fields.Char("Your Benefits as Donor 1 (EN)")
        receivew_2_en = fields.Char("Your Benefits as Donor 2 (EN)")
        receivew_3_en = fields.Char("Your Benefits as Donor 3 (EN)")
        receivew_4_en = fields.Char("Your Benefits as Donor 4 (EN)")

        photo = fields.Binary("Community Photo")
        photo_filename = fields.Char("Photo Filename")

        progress_percentage_en = fields.Char("Progress (%) (EN)")
        time_save_en = fields.Char("Time Saved (EN)")
        year_from_en = fields.Integer("From Year (EN)", default=lambda self: datetime.now().year)
        year_to_en = fields.Integer("To Year (EN)", default=lambda self: datetime.now().year)

        # Extra English Fields
        storage_capacity_en = fields.Char("Storage Capacity (EN)")
        system_capacity_en = fields.Char("System Capacity (EN)")
        facility_capacity_en = fields.Char("Facility Capacity (EN)")
        equipment_capacity_en = fields.Char("Equipment Capacity (EN)")
        fuel_cost_savings_en = fields.Char("Fuel-Cost Savings (per household) (EN)")
        environmental_impact_en = fields.Text("Environmental Impact (EN)")
        processing_capacity_per_year_en = fields.Char("Processing Capacity per Year (EN)")
        agricultural_impact_en = fields.Text("Agricultural Impact (EN)")
        economic_impact_en = fields.Text("Economic Impact (EN)")
        production_capacity_en = fields.Char("Production Capacity (EN)")
        production_impact_en = fields.Text("Production Impact (EN)")
        health_impact_en = fields.Text("Health Impact (EN)")

        community_liberia_file_en = fields.Binary("Attached File (EN)")
        community_file_filename_en = fields.Char("File Name (EN)")

        # -------------------------
        # German Fields (GER)
        # -------------------------
        month_from_de = fields.Selection([
            ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
            ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
            ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'),
        ], string="From Month (GER)")

        month_to_de = fields.Selection([
            ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
            ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
            ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'),
        ], string="To Month (GER)")

        name_de = fields.Char("Community Name (GER)", required=True)
        plot_project_de = fields.Char("Project Name (GER)")
        location_de = fields.Char("Location (GER)")
        number_beneficiaries_de = fields.Char("Number of Beneficiaries (GER)")
        distribution_de = fields.Text("Project Detail (GER)")
        duration_de = fields.Char("Duration (GER)", compute="_compute_duration_de", store=True)

        budget_de = fields.Char("Budget (GER)")
        beneficiaries_de = fields.Char("Beneficiaries (GER)")
        investment_needed_de = fields.Char("Investment Needed ($) (GER)")
        current_income_de = fields.Char("Current Avg Monthly Income ($) (GER)")
        additional_income_de = fields.Char("Expected Income from Project ($) (GER)")

        receivew_1_de = fields.Char("Your Benefits as Donor 1 (GER)")
        receivew_2_de = fields.Char("Your Benefits as Donor 2 (GER)")
        receivew_3_de = fields.Char("Your Benefits as Donor 3 (GER)")
        receivew_4_de = fields.Char("Your Benefits as Donor 4 (GER)")
        progress_percentage_de = fields.Char("Progress (%) (GER)")
        time_save_de = fields.Char("Time Saved (GER)")
        year_from_de = fields.Integer("From Year (GER)", default=lambda self: datetime.now().year)
        year_to_de = fields.Integer("To Year (GER)", default=lambda self: datetime.now().year)

        # Extra German fields
        storage_capacity_de = fields.Char("Storage Capacity (GER)")
        system_capacity_de = fields.Char("System Capacity (GER)")
        facility_capacity_de = fields.Char("Facility Capacity (GER)")
        equipment_capacity_de = fields.Char("Equipment Capacity (GER)")
        fuel_cost_savings_de = fields.Char("Fuel-Cost Savings (per household) (GER)")
        environmental_impact_de = fields.Text("Environmental Impact (GER)")
        processing_capacity_per_year_de = fields.Char("Processing Capacity per Year (GER)")
        agricultural_impact_de = fields.Text("Agricultural Impact (GER)")
        economic_impact_de = fields.Text("Economic Impact (GER)")
        production_capacity_de = fields.Char("Production Capacity (GER)")
        production_impact_de = fields.Text("Production Impact (GER)")
        health_impact_de = fields.Text("Health Impact (GER)")

        community_liberia_file_de = fields.Binary("Attached File (GER)")
        community_file_filename_de = fields.Char("File Name (GER)")

        # -------------------------
        # Capitalization Logic
        # -------------------------
        @api.model
        def create(self, vals):
            if vals.get('name_de'):
                vals['name_de'] = vals['name_de'].upper()
            return super().create(vals)

        def write(self, vals):
            if vals.get('name_de'):
                vals['name_de'] = vals['name_de'].upper()
            return super().write(vals)

        # -------------------------
        # Duration Compute (EN)
        # -------------------------
        @api.depends('month_from_en', 'month_to_en', 'year_from_en', 'year_to_en')
        def _compute_duration_en(self):
            months = {
                '1': 'Jan', '2': 'Feb', '3': 'Mar', '4': 'Apr',
                '5': 'May', '6': 'Jun', '7': 'Jul', '8': 'Aug',
                '9': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
            }
            for rec in self:
                if rec.month_from_en and rec.month_to_en:
                    rec.duration_en = f"{months[rec.month_from_en]} {rec.year_from_en} - {months[rec.month_to_en]} {rec.year_to_en}"
                else:
                    rec.duration_en = ""

        # -------------------------
        # Duration (GER)
        # -------------------------
        @api.depends('month_from_de', 'month_to_de', 'year_from_de', 'year_to_de')
        def _compute_duration_de(self):
            months = {
                '1': 'Jan', '2': 'Feb', '3': 'Mar', '4': 'Apr',
                '5': 'May', '6': 'Jun', '7': 'Jul', '8': 'Aug',
                '9': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
            }
            for rec in self:
                if rec.month_from_de and rec.month_to_de:
                    rec.duration_de = f"{months[rec.month_from_de]} {rec.year_from_de} - {months[rec.month_to_de]} {rec.year_to_de}"
                else:
                    rec.duration_de = ""


class SierraCommunity(models.Model):
    _name = 'sierra.community'
    _description = 'Sierra Community Project'
    _order = 'id desc'
    _rec_name = "name_en"

    # -------------------------
    # English Fields (EN)
    # -------------------------
    month_from_en = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string="From Month (EN)")

    month_to_en = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string="To Month (EN)")

    name_en = fields.Char("Community Name (EN)", required=True)
    plot_project_en = fields.Char("Project Name (EN)")
    location_en = fields.Char("Location (EN)")
    number_beneficiaries_en = fields.Char("Number of Beneficiaries (EN)")
    distribution_en = fields.Text("Project Detail (EN)")
    duration_en = fields.Char("Duration (EN)", compute="_compute_duration_en", store=True)

    budget_en = fields.Char("Budget (EN)")
    beneficiaries_en = fields.Char("Beneficiaries (EN)")
    investment_needed_en = fields.Char("Investment Needed ($) (EN)")
    current_income_en = fields.Char("Current Avg Monthly Income ($) (EN)")
    additional_income_en = fields.Char("Expected Income from Project ($) (EN)")

    receivew_1_en = fields.Char("Your Benefits as Donor 1 (EN)")
    receivew_2_en = fields.Char("Your Benefits as Donor 2 (EN)")
    receivew_3_en = fields.Char("Your Benefits as Donor 3 (EN)")
    receivew_4_en = fields.Char("Your Benefits as Donor 4 (EN)")

    photo = fields.Binary("Community Photo")
    photo_filename = fields.Char("Photo Filename")

    progress_percentage_en = fields.Char("Progress (%) (EN)")
    time_save_en = fields.Char("Time Saved (EN)")
    year_from_en = fields.Integer("From Year (EN)", default=lambda self: datetime.now().year)
    year_to_en = fields.Integer("To Year (EN)", default=lambda self: datetime.now().year)

    # Extra English Fields
    storage_capacity_en = fields.Char("Storage Capacity (EN)")
    system_capacity_en = fields.Char("System Capacity (EN)")
    facility_capacity_en = fields.Char("Facility Capacity (EN)")
    equipment_capacity_en = fields.Char("Equipment Capacity (EN)")
    fuel_cost_savings_en = fields.Char("Fuel-Cost Savings (per household) (EN)")
    environmental_impact_en = fields.Text("Environmental Impact (EN)")
    processing_capacity_per_year_en = fields.Char("Processing Capacity per Year (EN)")
    agricultural_impact_en = fields.Text("Agricultural Impact (EN)")
    economic_impact_en = fields.Text("Economic Impact (EN)")
    production_capacity_en = fields.Char("Production Capacity (EN)")
    production_impact_en = fields.Text("Production Impact (EN)")
    health_impact_en = fields.Text("Health Impact (EN)")

    community_sierra_file_en = fields.Binary("Attached File (EN)")
    community_file_filename_en = fields.Char("File Name (EN)")

    # -------------------------
    # German Fields (GER)
    # -------------------------
    month_from_de = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string="From Month (GER)")

    month_to_de = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string="To Month (GER)")

    name_de = fields.Char("Community Name (GER)", required=True)
    plot_project_de = fields.Char("Project Name (GER)")
    location_de = fields.Char("Location (GER)")
    number_beneficiaries_de = fields.Char("Number of Beneficiaries (GER)")
    distribution_de = fields.Text("Project Detail (GER)")
    duration_de = fields.Char("Duration (GER)", compute="_compute_duration_de", store=True)

    budget_de = fields.Char("Budget (GER)")
    beneficiaries_de = fields.Char("Beneficiaries (GER)")
    investment_needed_de = fields.Char("Investment Needed ($) (GER)")
    current_income_de = fields.Char("Current Avg Monthly Income ($) (GER)")
    additional_income_de = fields.Char("Expected Income from Project ($) (GER)")

    receivew_1_de = fields.Char("Your Benefits as Donor 1 (GER)")
    receivew_2_de = fields.Char("Your Benefits as Donor 2 (GER)")
    receivew_3_de = fields.Char("Your Benefits as Donor 3 (GER)")
    receivew_4_de = fields.Char("Your Benefits as Donor 4 (GER)")
    progress_percentage_de = fields.Char("Progress (%) (GER)")
    time_save_de = fields.Char("Time Saved (GER)")
    year_from_de = fields.Integer("From Year (GER)", default=lambda self: datetime.now().year)
    year_to_de = fields.Integer("To Year (GER)", default=lambda self: datetime.now().year)

    # Extra German fields
    storage_capacity_de = fields.Char("Storage Capacity (GER)")
    system_capacity_de = fields.Char("System Capacity (GER)")
    facility_capacity_de = fields.Char("Facility Capacity (GER)")
    equipment_capacity_de = fields.Char("Equipment Capacity (GER)")
    fuel_cost_savings_de = fields.Char("Fuel-Cost Savings (per household) (GER)")
    environmental_impact_de = fields.Text("Environmental Impact (GER)")
    processing_capacity_per_year_de = fields.Char("Processing Capacity per Year (GER)")
    agricultural_impact_de = fields.Text("Agricultural Impact (GER)")
    economic_impact_de = fields.Text("Economic Impact (GER)")
    production_capacity_de = fields.Char("Production Capacity (GER)")
    production_impact_de = fields.Text("Production Impact (GER)")
    health_impact_de = fields.Text("Health Impact (GER)")

    community_sierra_file_de = fields.Binary("Attached File (GER)")
    community_file_filename_de = fields.Char("File Name (GER)")

    # -------------------------
    # Capitalization Logic
    # -------------------------
    @api.model
    def create(self, vals):
        if vals.get('name_de'):
            vals['name_de'] = vals['name_de'].upper()
        return super().create(vals)

    def write(self, vals):
        if vals.get('name_de'):
            vals['name_de'] = vals['name_de'].upper()
        return super().write(vals)

    # -------------------------
    # Duration Compute (EN)
    # -------------------------
    @api.depends('month_from_en', 'month_to_en', 'year_from_en', 'year_to_en')
    def _compute_duration_en(self):
        months = {
            '1': 'Jan', '2': 'Feb', '3': 'Mar', '4': 'Apr',
            '5': 'May', '6': 'Jun', '7': 'Jul', '8': 'Aug',
            '9': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
        }
        for rec in self:
            if rec.month_from_en and rec.month_to_en:
                rec.duration_en = f"{months[rec.month_from_en]} {rec.year_from_en} - {months[rec.month_to_en]} {rec.year_to_en}"
            else:
                rec.duration_en = ""

    # -------------------------
    # Duration (GER)
    # -------------------------
    @api.depends('month_from_de', 'month_to_de', 'year_from_de', 'year_to_de')
    def _compute_duration_de(self):
        months = {
            '1': 'Jan', '2': 'Feb', '3': 'Mar', '4': 'Apr',
            '5': 'May', '6': 'Jun', '7': 'Jul', '8': 'Aug',
            '9': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
        }
        for rec in self:
            if rec.month_from_de and rec.month_to_de:
                rec.duration_de = f"{months[rec.month_from_de]} {rec.year_from_de} - {months[rec.month_to_de]} {rec.year_to_de}"
            else:
                rec.duration_de = ""


class AfghanistanCommunity(models.Model):
    _name = 'afghanistan.community'
    _description = 'Afghanistan Community Project'
    _order = 'id desc'
    _rec_name = "name_en"

    # -------------------------
    # English Fields (EN)
    # -------------------------
    month_from_en = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string="From Month (EN)")

    month_to_en = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string="To Month (EN)")

    name_en = fields.Char("Community Name (EN)", required=True)
    plot_project_en = fields.Char("Project Name (EN)")
    location_en = fields.Char("Location (EN)")
    number_beneficiaries_en = fields.Char("Number of Beneficiaries (EN)")
    distribution_en = fields.Text("Project Detail (EN)")
    duration_en = fields.Char("Duration (EN)", compute="_compute_duration_en", store=True)

    budget_en = fields.Char("Budget (EN)")
    beneficiaries_en = fields.Char("Beneficiaries (EN)")
    investment_needed_en = fields.Char("Investment Needed ($) (EN)")
    current_income_en = fields.Char("Current Avg Monthly Income ($) (EN)")
    additional_income_en = fields.Char("Expected Income from Project ($) (EN)")

    receivew_1_en = fields.Char("Your Benefits as Donor 1 (EN)")
    receivew_2_en = fields.Char("Your Benefits as Donor 2 (EN)")
    receivew_3_en = fields.Char("Your Benefits as Donor 3 (EN)")
    receivew_4_en = fields.Char("Your Benefits as Donor 4 (EN)")

    photo = fields.Binary("Community Photo")
    photo_filename = fields.Char("Photo Filename")

    progress_percentage_en = fields.Char("Progress (%) (EN)")
    time_save_en = fields.Char("Time Saved (EN)")
    year_from_en = fields.Integer("From Year (EN)", default=lambda self: datetime.now().year)
    year_to_en = fields.Integer("To Year (EN)", default=lambda self: datetime.now().year)

    # Extra English Fields
    storage_capacity_en = fields.Char("Storage Capacity (EN)")
    system_capacity_en = fields.Char("System Capacity (EN)")
    facility_capacity_en = fields.Char("Facility Capacity (EN)")
    equipment_capacity_en = fields.Char("Equipment Capacity (EN)")
    fuel_cost_savings_en = fields.Char("Fuel-Cost Savings (per household) (EN)")
    environmental_impact_en = fields.Text("Environmental Impact (EN)")
    processing_capacity_per_year_en = fields.Char("Processing Capacity per Year (EN)")
    agricultural_impact_en = fields.Text("Agricultural Impact (EN)")
    economic_impact_en = fields.Text("Economic Impact (EN)")
    production_capacity_en = fields.Char("Production Capacity (EN)")
    production_impact_en = fields.Text("Production Impact (EN)")
    health_impact_en = fields.Text("Health Impact (EN)")

    community_afghanistan_file_en = fields.Binary("Attached File (EN)")
    community_file_filename_en = fields.Char("File Name (EN)")

    # -------------------------
    # German Fields (GER)
    # -------------------------
    month_from_de = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string="From Month (GER)")

    month_to_de = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string="To Month (GER)")

    name_de = fields.Char("Community Name (GER)", required=True)
    plot_project_de = fields.Char("Project Name (GER)")
    location_de = fields.Char("Location (GER)")
    number_beneficiaries_de = fields.Char("Number of Beneficiaries (GER)")
    distribution_de = fields.Text("Project Detail (GER)")
    duration_de = fields.Char("Duration (GER)", compute="_compute_duration_de", store=True)

    budget_de = fields.Char("Budget (GER)")
    beneficiaries_de = fields.Char("Beneficiaries (GER)")
    investment_needed_de = fields.Char("Investment Needed ($) (GER)")
    current_income_de = fields.Char("Current Avg Monthly Income ($) (GER)")
    additional_income_de = fields.Char("Expected Income from Project ($) (GER)")

    receivew_1_de = fields.Char("Your Benefits as Donor 1 (GER)")
    receivew_2_de = fields.Char("Your Benefits as Donor 2 (GER)")
    receivew_3_de = fields.Char("Your Benefits as Donor 3 (GER)")
    receivew_4_de = fields.Char("Your Benefits as Donor 4 (GER)")
    progress_percentage_de = fields.Char("Progress (%) (GER)")
    time_save_de = fields.Char("Time Saved (GER)")
    year_from_de = fields.Integer("From Year (GER)", default=lambda self: datetime.now().year)
    year_to_de = fields.Integer("To Year (GER)", default=lambda self: datetime.now().year)

    # Extra German fields
    storage_capacity_de = fields.Char("Storage Capacity (GER)")
    system_capacity_de = fields.Char("System Capacity (GER)")
    facility_capacity_de = fields.Char("Facility Capacity (GER)")
    equipment_capacity_de = fields.Char("Equipment Capacity (GER)")
    fuel_cost_savings_de = fields.Char("Fuel-Cost Savings (per household) (GER)")
    environmental_impact_de = fields.Text("Environmental Impact (GER)")
    processing_capacity_per_year_de = fields.Char("Processing Capacity per Year (GER)")
    agricultural_impact_de = fields.Text("Agricultural Impact (GER)")
    economic_impact_de = fields.Text("Economic Impact (GER)")
    production_capacity_de = fields.Char("Production Capacity (GER)")
    production_impact_de = fields.Text("Production Impact (GER)")
    health_impact_de = fields.Text("Health Impact (GER)")

    community_afghanistan_file_de = fields.Binary("Attached File (GER)")
    community_file_filename_de = fields.Char("File Name (GER)")

    # -------------------------
    # Capitalization Logic
    # -------------------------
    @api.model
    def create(self, vals):
        if vals.get('name_de'):
            vals['name_de'] = vals['name_de'].upper()
        return super().create(vals)

    def write(self, vals):
        if vals.get('name_de'):
            vals['name_de'] = vals['name_de'].upper()
        return super().write(vals)

    # -------------------------
    # Duration Compute (EN)
    # -------------------------
    @api.depends('month_from_en', 'month_to_en', 'year_from_en', 'year_to_en')
    def _compute_duration_en(self):
        months = {
            '1': 'Jan', '2': 'Feb', '3': 'Mar', '4': 'Apr',
            '5': 'May', '6': 'Jun', '7': 'Jul', '8': 'Aug',
            '9': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
        }
        for rec in self:
            if rec.month_from_en and rec.month_to_en:
                rec.duration_en = f"{months[rec.month_from_en]} {rec.year_from_en} - {months[rec.month_to_en]} {rec.year_to_en}"
            else:
                rec.duration_en = ""

    # -------------------------
    # Duration (GER)
    # -------------------------
    @api.depends('month_from_de', 'month_to_de', 'year_from_de', 'year_to_de')
    def _compute_duration_de(self):
        months = {
            '1': 'Jan', '2': 'Feb', '3': 'Mar', '4': 'Apr',
            '5': 'May', '6': 'Jun', '7': 'Jul', '8': 'Aug',
            '9': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
        }
        for rec in self:
            if rec.month_from_de and rec.month_to_de:
                rec.duration_de = f"{months[rec.month_from_de]} {rec.year_from_de} - {months[rec.month_to_de]} {rec.year_to_de}"
            else:
                rec.duration_de = ""
