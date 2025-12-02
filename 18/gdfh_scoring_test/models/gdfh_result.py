from odoo import models, fields, api
from odoo.exceptions import UserError


class GdfhResult(models.Model):
    _name = 'gdfh.result'
    _description = 'GDfH Scoring Test Result'
    _order = 'submitted_on desc'

    # Basic Info
    name = fields.Char(string="Name", required=True, copy=False)
    email = fields.Char(string="Email", required=True, copy=False)
    country = fields.Char(string="Country")

    # Individual Scores (1 to 18)
    score_1 = fields.Integer("Global Awareness 1")
    score_2 = fields.Integer("Global Awareness 2")
    score_3 = fields.Integer("Global Awareness 3")

    score_4 = fields.Integer("Civic Participation 1")
    score_5 = fields.Integer("Civic Participation 2")
    score_6 = fields.Integer("Civic Participation 3")

    score_7 = fields.Integer("Environment Protection 1")
    score_8 = fields.Integer("Environment Protection 2")
    score_9 = fields.Integer("Environment Protection 3")

    score_10 = fields.Integer("Ethical Consumption 1")
    score_11 = fields.Integer("Ethical Consumption 2")
    score_12 = fields.Integer("Ethical Consumption 3")

    score_13 = fields.Integer("Peace and Conflict 1")
    score_14 = fields.Integer("Peace and Conflict 2")
    score_15 = fields.Integer("Peace and Conflict 3")

    score_16 = fields.Integer("Intercultural Competence 1")
    score_17 = fields.Integer("Intercultural Competence 2")
    score_18 = fields.Integer("Intercultural Competence 3")

    # Computed Scores
    total_score = fields.Integer(
        string="Total Score (out of 180)",
        compute="_compute_total_score",
        store=True
    )

    level = fields.Text(
        string="Level",
        compute="_compute_level",
        store=True
    )

    # Group Scores
    global_awareness = fields.Integer(compute="_compute_total_score", store=True)
    civic_participation = fields.Integer(compute="_compute_total_score", store=True)
    environment = fields.Integer(compute="_compute_total_score", store=True)
    ethical = fields.Integer(compute="_compute_total_score", store=True)
    peace = fields.Integer(compute="_compute_total_score", store=True)
    intercultural = fields.Integer(compute="_compute_total_score", store=True)

    # Percentages
    global_awareness_pct = fields.Float(compute="_compute_total_score", store=True)
    civic_participation_pct = fields.Float(compute="_compute_total_score", store=True)
    environment_pct = fields.Float(compute="_compute_total_score", store=True)
    ethical_pct = fields.Float(compute="_compute_total_score", store=True)
    peace_pct = fields.Float(compute="_compute_total_score", store=True)
    intercultural_pct = fields.Float(compute="_compute_total_score", store=True)

    submitted_on = fields.Datetime(
        string="Submitted On",
        default=fields.Datetime.now,
        readonly=True
    )

    # Link to Email Group
    email_group_id = fields.Many2one(
        "gdfh.email.group",
        string="Email Group",
        ondelete="set null"
    )

    # Auto-create/find email group
    @api.model
    def create(self, vals):
        email = vals.get("email")
        if email:
            group = self.env["gdfh.email.group"].search([("email", "=", email)], limit=1)
            if not group:
                group = self.env["gdfh.email.group"].create({"email": email})
            vals["email_group_id"] = group.id

        return super().create(vals)

    # Compute Total + Group Scores + Percentages
    @api.depends(
        'score_1', 'score_2', 'score_3',
        'score_4', 'score_5', 'score_6',
        'score_7', 'score_8', 'score_9',
        'score_10', 'score_11', 'score_12',
        'score_13', 'score_14', 'score_15',
        'score_16', 'score_17', 'score_18'
    )
    def _compute_total_score(self):
        for rec in self:

            # Sum group scores
            groups = {
                'global_awareness': sum([rec.score_1 or 0, rec.score_2 or 0, rec.score_3 or 0]),
                'civic_participation': sum([rec.score_4 or 0, rec.score_5 or 0, rec.score_6 or 0]),
                'environment': sum([rec.score_7 or 0, rec.score_8 or 0, rec.score_9 or 0]),
                'ethical': sum([rec.score_10 or 0, rec.score_11 or 0, rec.score_12 or 0]),
                'peace': sum([rec.score_13 or 0, rec.score_14 or 0, rec.score_15 or 0]),
                'intercultural': sum([rec.score_16 or 0, rec.score_17 or 0, rec.score_18 or 0]),
            }

            # Assign group scores
            rec.global_awareness = groups['global_awareness']
            rec.civic_participation = groups['civic_participation']
            rec.environment = groups['environment']
            rec.ethical = groups['ethical']
            rec.peace = groups['peace']
            rec.intercultural = groups['intercultural']

            # Percentages (each group max = 30)
            max_group = 30.0

            rec.global_awareness_pct = round((groups['global_awareness'] / max_group) * 100)
            rec.civic_participation_pct = round((groups['civic_participation'] / max_group) * 100)
            rec.environment_pct = round((groups['environment'] / max_group) * 100)
            rec.ethical_pct = round((groups['ethical'] / max_group) * 100)
            rec.peace_pct = round((groups['peace'] / max_group) * 100)
            rec.intercultural_pct = round((groups['intercultural'] / max_group) * 100)

            # Total
            rec.total_score = sum(groups.values())

    # Compute Level
    @api.depends('total_score')
    def _compute_level(self):
        for rec in self:
            score = rec.total_score

            if score >= 150:
                rec.level = (
                    "Progressive Visionary: Your actions profoundly align with and actively "
                    "advance a progressive world."
                )
            elif score >= 120:
                rec.level = (
                    "Strong Contributor: You consistently contribute meaningfully toward "
                    "a progressive world."
                )
            elif score >= 90:
                rec.level = (
                    "Emerging Contributor: You are on the path of contributing to a "
                    "progressive world."
                )
            else:
                rec.level = (
                    "Needs Focused Engagement: There is room for growth and deeper involvement."
                )

    # Print PDF Report
    def print_report(self):
        if len(self) != 1:
            raise UserError("Please select a single record to print.")
        return self.env.ref('gdfh_scoring_test.action_report_gdfh_result').report_action(self)
