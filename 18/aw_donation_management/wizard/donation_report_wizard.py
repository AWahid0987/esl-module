from odoo import models, fields, api
from datetime import datetime, date
import calendar


class DonationReportWizard(models.TransientModel):
    _name = 'donation.report.wizard'
    _description = 'Donation Report Wizard'

    # NEW FILTER FIELDS (replacing month/year)
    date_start = fields.Date('Start Date', required=True, default=lambda self: date.today().replace(day=1))
    date_end = fields.Date('End Date', required=True, default=lambda self: date.today())

    # Payment status filters
    paid = fields.Boolean('Paid', default=False)
    unpaid = fields.Boolean('UnPaid', default=False)
    total = fields.Boolean('Total', default=True)

    # Multi-company selection
    company_ids = fields.Many2many(
        'res.company',
        string="Companies",
        default=lambda self: self._default_companies()
    )

    @api.model
    def _default_companies(self):
        """Auto-select the same companies selected in the top-right multi-company switcher."""
        allowed = self.env.context.get("allowed_company_ids")
        if allowed:
            return [(6, 0, allowed)]
        return [(6, 0, [self.env.company.id])]

    @api.onchange('paid', 'unpaid', 'total')
    def _onchange_payment_status(self):
        """Ensure only one payment status is selected at a time"""
        if self.paid:
            self.unpaid = False
            self.total = False
        elif self.unpaid:
            self.paid = False
            self.total = False
        elif self.total:
            self.paid = False
            self.unpaid = False

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        """Validate date range"""
        for record in self:
            if record.date_start and record.date_end:
                if record.date_start > record.date_end:
                    raise models.ValidationError('Start date must be before or equal to end date.')

    def _get_payment_status_domain(self):
        """Get domain filter based on payment status selection"""
        if self.paid:
            return [('state', '=', 'paid')]
        elif self.unpaid:
            return [('state', 'in', ['draft', 'confirmed', 'pending'])]
        else:  # total - all records
            return []

    def find_available_accounts(self):
        """Find what accounts are actually available and check journal entries"""
        try:
            # Get all accounts
            all_accounts = self.env['account.account'].search([])

            # Look for donation-related accounts
            donation_related = self.env['account.account'].search([
                '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|',
                '|', '|',
                ('name', 'ilike', 'donation'),
                ('name', 'ilike', 'zakat'),
                ('name', 'ilike', 'fitrana'),
                ('name', 'ilike', 'fidya'),
                ('name', 'ilike', 'hadiya_imam_hussain'),
                ('name', 'ilike', 'sadqa_mulaqat'),
                ('name', 'ilike', 'multan_sharif_fund'),
                ('name', 'ilike', 'naat_khaani'),
                ('name', 'ilike', 'qurbani_wala_mamla'),
                ('name', 'ilike', 'sadqa_shifa'),
                ('name', 'ilike', 'special_fund_lahore'),
                ('name', 'ilike', 'hadia'),
                ('name', 'ilike', 'langer_shareef_multan'),
                ('name', 'ilike', 'langer_shareef'),
                ('name', 'ilike', 'syedi_g_ki_neeyat_se_sadqa'),
                ('name', 'ilike', 'hadia_aqa_ji'),
                ('name', 'ilike', 'faisal_town_purchase_fund'),
                ('name', 'ilike', 'qurbani_zati'),
                ('name', 'ilike', 'qurbani_sarkari'),
                ('name', 'ilike', 'hadia_saad_bin_waqas'),
                ('name', 'ilike', 'hadia_ameer_hamza'),
                ('name', 'ilike', 'sadqa'),
                ('name', 'ilike', 'revenue')
            ])

            # Look for revenue accounts (4xxxx) excluding non-donation accounts
            revenue_accounts = self.env['account.account'].search([
                ('code', '=like', '4%'),
                ('code', 'not in', ['441000', '442000', '443000', '450000'])
            ])

            # Look for specific accounts 40001-40023
            specific_codes = [f'4000{i}' if i < 10 else f'400{i}' for i in range(1, 24)]
            specific_accounts = self.env['account.account'].search([('code', 'in', specific_codes)])

            # Count journal entries for the period (using date_start and date_end)
            journal_entries = self.env['account.move.line'].search([
                ('date', '>=', self.date_start),
                ('date', '<=', self.date_end),
                ('account_id', 'in', revenue_accounts.ids),
                ('credit', '>', 0)
            ])

            message = f"""
=== ACCOUNT AND JOURNAL ENTRY ANALYSIS ===

Total Accounts: {len(all_accounts)}
Donation-Related Accounts: {len(donation_related)}
Revenue Accounts (4xxxx, excluding 441000-450000): {len(revenue_accounts)}
Specific Accounts (40001-40023): {len(specific_accounts)}
Journal Entries for {self.date_start} to {self.date_end}: {len(journal_entries)}

DONATION-RELATED ACCOUNTS:
"""

            for acc in donation_related:
                message += f"  {acc.code} - {acc.name}\n"

            message += f"\nREVENUE ACCOUNTS (donation-related only):\n"
            for acc in revenue_accounts:
                message += f"  {acc.code} - {acc.name}\n"

            if specific_accounts:
                message += f"\nSPECIFIC DONATION ACCOUNTS (40001-40023):\n"
                for acc in specific_accounts:
                    message += f"  {acc.code} - {acc.name}\n"
            else:
                message += f"\nNO SPECIFIC DONATION ACCOUNTS (40001-40023) FOUND\n"

            # Show sample journal entries
            if journal_entries:
                message += f"\nSAMPLE JOURNAL ENTRIES ({self.date_start} to {self.date_end}):\n"
                for entry in journal_entries[:5]:
                    message += f"  Account: {entry.account_id.code} - {entry.account_id.name}, Credit: {entry.credit}, Ref: {entry.ref or 'N/A'}\n"
            else:
                message += f"\nNO JOURNAL ENTRIES FOUND FOR THE PERIOD\n"

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Account & Journal Entry Analysis',
                    'message': message,
                    'type': 'info',
                    'sticky': True
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Analysis Error',
                    'message': f'Error: {str(e)}',
                    'type': 'danger'
                }
            }

    def _categorize_journal_entry_amount(self, journal_line):
        """Categorize journal entry amount based on account name, reference, or label"""
        amount = journal_line.credit or 0.0  # Use credit for income

        # Initialize all categories
        categories = {
            'zakat': 0, 'fidya': 0, 'sadqa': 0, 'fitrana': 0,
            'hadiya_imam_hussain': 0, 'sadqa_mulaqat': 0, 'multan_sharif_fund': 0,
            'naat_khaani': 0, 'qurbani_wala_mamla': 0, 'hadia': 0,
            'sadqa_shifa': 0, 'special_fund_lahore': 0, 'hadia_saad_bin_waqas': 0,
            'hadia_ameer_hamza': 0, 'langer_shareef_multan': 0, 'langer_shareef': 0,
            'syedi_g_ki_neeyat_se_sadqa': 0, 'hadia_aqa_ji': 0,
            'faisal_town_purchase_fund': 0, 'qurbani_zati': 0, 'qurbani_sarkari': 0
        }

        # Check account name first
        if journal_line.account_id and journal_line.account_id.name:
            account_name = journal_line.account_id.name.lower()
            for category in categories.keys():
                if category.replace('_', ' ') in account_name or category in account_name:
                    categories[category] = amount
                    return categories

        # Check reference/description fields
        text_fields = [journal_line.ref, journal_line.name, getattr(journal_line, 'label', None)]
        for text_field in text_fields:
            if text_field:
                text_content = str(text_field).lower()
                for category in categories.keys():
                    if category.replace('_', ' ') in text_content or category in text_content:
                        categories[category] = amount
                        return categories

        # Check if linked to donation order
        if hasattr(journal_line, 'donation_id') and journal_line.donation_id:
            donation = journal_line.donation_id
            if hasattr(donation, 'donation_type') and donation.donation_type:
                donation_type = str(donation.donation_type).lower().strip()
                if donation_type in categories:
                    categories[donation_type] = amount
                    return categories

        # Default to sadqa if no specific type found
        categories['sadqa'] = amount
        return categories

    def generate_report_from_journal_entries(self):
        """Generate report from journal entries (account.move.line) - SAME LOGIC, NEW FILTERS"""
        try:
            # Validate inputs
            if not self.date_start or not self.date_end:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Missing Information',
                        'message': 'Please select both start and end dates.',
                        'type': 'warning'
                    }
                }

            if not self.company_ids:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Missing Information',
                        'message': 'Please select at least one company.',
                        'type': 'warning'
                    }
                }

            # Store month/year for report records
            month_str = str(self.date_start.month)
            year_str = str(self.date_start.year)

            # Clear old data
            domain = [('month', '=', month_str), ('year', '=', year_str)]
            self.env['donation.account.report'].search(domain).unlink()

            # Get selected companies
            companies = self.company_ids

            # Find donation-related accounts (excluding non-donation accounts)
            accounts = self.env['account.account'].search([
                ('code', '=like', '4%'),
                ('code', 'not in', ['441000', '442000', '443000', '450000'])
            ])

            if not accounts:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'No Accounts Found',
                        'message': 'No donation-related revenue accounts found in the system.',
                        'type': 'warning'
                    }
                }

            report_created = False
            total_amount_processed = 0
            entries_processed = 0

            for company in companies:
                for account in accounts:
                    # Search journal entries for this company and account using date_start/date_end
                    journal_domain = [
                        ('company_id', '=', company.id),
                        ('account_id', '=', account.id),
                        ('date', '>=', self.date_start),
                        ('date', '<=', self.date_end),
                        ('credit', '>', 0),  # Only credit entries (income)
                        ('move_id.state', '=', 'posted')  # Only posted entries
                    ]

                    journal_lines = self.env['account.move.line'].search(journal_domain)

                    if journal_lines:
                        # Initialize totals for all categories
                        totals = {
                            'zakat': 0, 'fidya': 0, 'sadqa': 0, 'fitrana': 0, 'hadiya_imam_hussain': 0,
                            'sadqa_mulaqat': 0, 'multan_sharif_fund': 0, 'naat_khaani': 0, 'qurbani_wala_mamla': 0,
                            'hadia': 0, 'sadqa_shifa': 0, 'special_fund_lahore': 0, 'hadia_saad_bin_waqas': 0,
                            'hadia_ameer_hamza': 0, 'langer_shareef_multan': 0, 'langer_shareef': 0,
                            'syedi_g_ki_neeyat_se_sadqa': 0, 'hadia_aqa_ji': 0, 'faisal_town_purchase_fund': 0,
                            'qurbani_zati': 0, 'qurbani_sarkari': 0
                        }

                        for journal_line in journal_lines:
                            # Use the journal entry categorization method
                            categories = self._categorize_journal_entry_amount(journal_line)
                            for category, amount in categories.items():
                                totals[category] += amount

                            total_amount_processed += journal_line.credit or 0.0
                            entries_processed += 1

                        # Create report record only if there are amounts
                        if any(totals.values()):
                            vals = {
                                'company_id': company.id,
                                'account_id': account.id,
                                'zakat': totals['zakat'],
                                'fidya': totals['fidya'],
                                'hadiya_imam_hussain': totals['hadiya_imam_hussain'],
                                'fitrana': totals['fitrana'],
                                'sadqa': totals['sadqa'],
                                'sadqa_mulaqat': totals['sadqa_mulaqat'],
                                'multan_sharif_fund': totals['multan_sharif_fund'],
                                'naat_khaani': totals['naat_khaani'],
                                'qurbani_wala_mamla': totals['qurbani_wala_mamla'],
                                'hadia': totals['hadia'],
                                'sadqa_shifa': totals['sadqa_shifa'],
                                'special_fund_lahore': totals['special_fund_lahore'],
                                'langer_shareef_multan': totals['langer_shareef_multan'],
                                'langer_shareef': totals['langer_shareef'],
                                'syedi_g_ki_neeyat_se_sadqa': totals['syedi_g_ki_neeyat_se_sadqa'],
                                'hadia_aqa_ji': totals['hadia_aqa_ji'],
                                'faisal_town_purchase_fund': totals['faisal_town_purchase_fund'],
                                'qurbani_zati': totals['qurbani_zati'],
                                'qurbani_sarkari': totals['qurbani_sarkari'],
                                'hadia_saad_bin_waqas': totals['hadia_saad_bin_waqas'],
                                'hadia_ameer_hamza': totals['hadia_ameer_hamza'],
                                'month': month_str,
                                'year': year_str,
                            }

                            self.env['donation.account.report'].create(vals)
                            report_created = True

            if not report_created:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'No Data Found',
                        'message': f'No journal entry data found for {self.date_start} to {self.date_end} with specified accounts.\nAccounts checked: {len(accounts)}',
                        'type': 'warning'
                    }
                }

            # Determine payment status for display
            payment_status = 'All'
            if self.paid:
                payment_status = 'Paid Only'
            elif self.unpaid:
                payment_status = 'Unpaid Only'

            # Show success message with stats
            success_message = f"""Report generated successfully!

Period: {self.date_start} to {self.date_end}
Payment Status: {payment_status}
Companies: {', '.join(companies.mapped('name'))}
Journal entries processed: {entries_processed}
Total amount: {total_amount_processed}
Accounts used: {len(accounts)} accounts"""

            return {
                'name': f'Donation Report - {self.date_start} to {self.date_end}',
                'type': 'ir.actions.act_window',
                'res_model': 'donation.account.report',
                'view_mode': 'tree,form',
                'domain': [
                    ('month', '=', month_str),
                    ('year', '=', year_str),
                    ('company_id', 'in', companies.ids)
                ],
                'target': 'current',
                'context': {
                    'group_by': ['company_id', 'account_id'],
                    'search_default_current_period': 1,
                }
            }

        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Filtered Report Error',
                    'message': f'Error: {str(e)}',
                    'type': 'danger'
                }
            }

    def generate_report(self):
        """Main generate report method - uses journal entries for complete data"""
        try:
            return self.generate_report_from_journal_entries()
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Report Generation Error',
                    'message': f'Error: {str(e)}',
                    'type': 'danger'
                }
            }

    def export_to_excel(self):
        """Export report data to Excel format"""
        try:
            import xlsxwriter
            import base64
            from io import BytesIO

            # Get report data using date range
            month_str = str(self.date_start.month)
            year_str = str(self.date_start.year)

            domain = [
                ('month', '=', month_str),
                ('year', '=', year_str),
                ('company_id', 'in', self.company_ids.ids)
            ]

            reports = self.env['donation.account.report'].search(domain)

            if not reports:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'No Data',
                        'message': 'No report data found to export. Please generate a report first.',
                        'type': 'warning'
                    }
                }

            # Create Excel file
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet('Donation Report')

            # Header format
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1
            })

            # Data format
            data_format = workbook.add_format({'border': 1})
            currency_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})

            # Headers
            headers = [
                'Company', 'Account Code', 'Account Name', 'Month', 'Year',
                'Zakat', 'Fidya', 'Fitrana', 'Sadqa', 'Hadiya Imam Hussain',
                'Sadqa Mulaqat', 'Multan Sharif Fund', 'Naat Khaani', 'Qurbani Wala Mamla',
                'Hadia', 'Sadqa Shifa', 'Special Fund Lahore', 'Hadia Saad Bin Waqas',
                'Hadia Ameer Hamza', 'Langer Shareef Multan', 'Langer Shareef',
                'Syedi G Ki Neeyat Se Sadqa', 'Hadia Aqa Ji', 'Faisal Town Purchase Fund',
                'Qurbani Zati', 'Qurbani Sarkari', 'Total'
            ]

            # Write headers
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)

            # Write data
            row = 1
            for report in reports:
                total = (report.zakat + report.fidya + report.fitrana + report.sadqa +
                         report.hadiya_imam_hussain + report.sadqa_mulaqat + report.multan_sharif_fund +
                         report.naat_khaani + report.qurbani_wala_mamla + report.hadia +
                         report.sadqa_shifa + report.special_fund_lahore + report.hadia_saad_bin_waqas +
                         report.hadia_ameer_hamza + report.langer_shareef_multan + report.langer_shareef +
                         report.syedi_g_ki_neeyat_se_sadqa + report.hadia_aqa_ji +
                         report.faisal_town_purchase_fund + report.qurbani_zati + report.qurbani_sarkari)

                data_row = [
                    report.company_id.name or '',
                    report.account_id.code or '',
                    report.account_id.name or '',
                    report.month,
                    report.year,
                    report.zakat, report.fidya, report.fitrana, report.sadqa,
                    report.hadiya_imam_hussain, report.sadqa_mulaqat, report.multan_sharif_fund,
                    report.naat_khaani, report.qurbani_wala_mamla, report.hadia,
                    report.sadqa_shifa, report.special_fund_lahore, report.hadia_saad_bin_waqas,
                    report.hadia_ameer_hamza, report.langer_shareef_multan, report.langer_shareef,
                    report.syedi_g_ki_neeyat_se_sadqa, report.hadia_aqa_ji,
                    report.faisal_town_purchase_fund, report.qurbani_zati, report.qurbani_sarkari,
                    total
                ]

                for col, value in enumerate(data_row):
                    if col >= 5:  # Currency columns
                        worksheet.write(row, col, value, currency_format)
                    else:
                        worksheet.write(row, col, value, data_format)

                row += 1

            # Auto-adjust column widths
            for col in range(len(headers)):
                worksheet.set_column(col, col, 15)

            workbook.close()
            output.seek(0)

            # Create attachment
            filename = f"donation_report_{self.date_start}_to_{self.date_end}.xlsx"

            attachment = self.env['ir.attachment'].create({
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(output.read()),
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            })

            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'new',
            }

        except ImportError:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Excel Export Not Available',
                    'message': 'xlsxwriter library not installed. Please install it to export to Excel.',
                    'type': 'warning'
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Export Error',
                    'message': f'Error exporting to Excel: {str(e)}',
                    'type': 'danger'
                }
            }

    def view_summary_report(self):
        """Generate and view summary report across all categories"""
        try:
            # Get report data using date range
            month_str = str(self.date_start.month)
            year_str = str(self.date_start.year)
            period_text = f"{self.date_start} to {self.date_end}"

            domain = [
                ('month', '=', month_str),
                ('year', '=', year_str),
                ('company_id', 'in', self.company_ids.ids)
            ]

            reports = self.env['donation.account.report'].search(domain)

            if not reports:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'No Data',
                        'message': 'No report data found. Please generate a report first.',
                        'type': 'warning'
                    }
                }

            # Calculate totals
            summary = {
                'zakat': sum(reports.mapped('zakat')),
                'fidya': sum(reports.mapped('fidya')),
                'fitrana': sum(reports.mapped('fitrana')),
                'sadqa': sum(reports.mapped('sadqa')),
                'hadiya_imam_hussain': sum(reports.mapped('hadiya_imam_hussain')),
                'sadqa_mulaqat': sum(reports.mapped('sadqa_mulaqat')),
                'multan_sharif_fund': sum(reports.mapped('multan_sharif_fund')),
                'naat_khaani': sum(reports.mapped('naat_khaani')),
                'qurbani_wala_mamla': sum(reports.mapped('qurbani_wala_mamla')),
                'hadia': sum(reports.mapped('hadia')),
                'sadqa_shifa': sum(reports.mapped('sadqa_shifa')),
                'special_fund_lahore': sum(reports.mapped('special_fund_lahore')),
                'hadia_saad_bin_waqas': sum(reports.mapped('hadia_saad_bin_waqas')),
                'hadia_ameer_hamza': sum(reports.mapped('hadia_ameer_hamza')),
                'langer_shareef_multan': sum(reports.mapped('langer_shareef_multan')),
                'langer_shareef': sum(reports.mapped('langer_shareef')),
                'syedi_g_ki_neeyat_se_sadqa': sum(reports.mapped('syedi_g_ki_neeyat_se_sadqa')),
                'hadia_aqa_ji': sum(reports.mapped('hadia_aqa_ji')),
                'faisal_town_purchase_fund': sum(reports.mapped('faisal_town_purchase_fund')),
                'qurbani_zati': sum(reports.mapped('qurbani_zati')),
                'qurbani_sarkari': sum(reports.mapped('qurbani_sarkari')),
            }

            # Calculate grand total
            grand_total = sum(summary.values())

            # Format summary message
            summary_message = f"""
=== DONATION SUMMARY REPORT ===
Period: {period_text}

"""

            for category, amount in summary.items():
                if amount > 0:
                    category_display = category.replace('_', ' ').title()
                    summary_message += f"{category_display}: {amount:,.2f}\n"

            summary_message += f"\nGRAND TOTAL: {grand_total:,.2f}"
            summary_message += f"\nTotal Records: {len(reports)}"

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': f'Summary Report - {period_text}',
                    'message': summary_message,
                    'type': 'success',
                    'sticky': True
                }
            }

        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Summary Report Error',
                    'message': f'Error: {str(e)}',
                    'type': 'danger'
                }
            }

    def print_report(self):
        """Print donation report"""
        try:
            # Get report data using date range
            month_str = str(self.date_start.month)
            year_str = str(self.date_start.year)

            domain = [
                ('month', '=', month_str),
                ('year', '=', year_str),
                ('company_id', 'in', self.company_ids.ids)
            ]

            reports = self.env['donation.account.report'].search(domain)

            if not reports:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'No Data',
                        'message': 'No report data found to print. Please generate a report first.',
                        'type': 'warning'
                    }
                }

            # Return print action
            return self.env.ref('your_module.action_donation_report_print').report_action(reports)

        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Print Error',
                    'message': f'Error printing report: {str(e)}',
                    'type': 'danger'
                }
            }

    def clear_all_reports(self):
        """Clear all existing donation reports"""
        try:
            all_reports = self.env['donation.account.report'].search([])
            count = len(all_reports)
            all_reports.unlink()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Reports Cleared',
                    'message': f'Successfully deleted {count} donation report records.',
                    'type': 'success'
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Clear Error',
                    'message': f'Error clearing reports: {str(e)}',
                    'type': 'danger'
                }
            }

    def test_journal_entries(self):
        """Test method to check journal entries without creating reports"""
        try:
            # Get all journal entries in the period using date_start/date_end
            all_entries = self.env['account.move.line'].search([
                ('date', '>=', self.date_start),
                ('date', '<=', self.date_end),
                ('credit', '>', 0),
                ('move_id.state', '=', 'posted')
            ])

            # Get donation-related entries
            donation_accounts = self.env['account.account'].search([
                ('code', '=like', '4%'),
                ('code', 'not in', ['441000', '442000', '443000', '450000'])
            ])

            donation_entries = self.env['account.move.line'].search([
                ('date', '>=', self.date_start),
                ('date', '<=', self.date_end),
                ('credit', '>', 0),
                ('move_id.state', '=', 'posted'),
                ('account_id', 'in', donation_accounts.ids)
            ])

            total_credit = sum(all_entries.mapped('credit'))
            donation_credit = sum(donation_entries.mapped('credit'))

            message = f"""
=== JOURNAL ENTRY TEST RESULTS ===
Period: {self.date_start} to {self.date_end}

All Journal Entries (Credit > 0): {len(all_entries)}
Total Credit Amount: {total_credit:,.2f}

Donation-Related Entries: {len(donation_entries)}
Donation Credit Amount: {donation_credit:,.2f}

Donation Accounts Found: {len(donation_accounts)}

SAMPLE DONATION ENTRIES:
"""

            for entry in donation_entries[:10]:
                message += f"  {entry.account_id.code} - {entry.account_id.name}: {entry.credit:,.2f} (Ref: {entry.ref or 'N/A'})\n"

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Journal Entry Test Results',
                    'message': message,
                    'type': 'info',
                    'sticky': True
                }
            }

        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Test Error',
                    'message': f'Error: {str(e)}',
                    'type': 'danger'
                }
            }
