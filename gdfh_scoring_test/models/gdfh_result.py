# models/gdfh_result.py
from odoo import models, fields, api
from odoo.exceptions import UserError

class GdfhResult(models.Model):
    _name = 'gdfh.result'
    _description = 'GDfH Scoring Test Result'
    _order = 'submitted_on desc'

    name = fields.Char(string="Name", required=True, copy=False)
    email = fields.Char(string="Email", required=True, copy=False)
    country = fields.Char(string="Country")

    # Individual Scores (1 to 18)
    score_1 = fields.Integer(string="Global Awareness 1")
    score_2 = fields.Integer(string="Global Awareness 2")
    score_3 = fields.Integer(string="Global Awareness 3")
    score_4 = fields.Integer(string="Civic Participation 1")
    score_5 = fields.Integer(string="Civic Participation 2")
    score_6 = fields.Integer(string="Civic Participation 3")
    score_7 = fields.Integer(string="Environment Protection 1")
    score_8 = fields.Integer(string="Environment Protection 2")
    score_9 = fields.Integer(string="Environment Protection 3")
    score_10 = fields.Integer(string="Ethical Consumption 1")
    score_11 = fields.Integer(string="Ethical Consumption 2")
    score_12 = fields.Integer(string="Ethical Consumption 3")
    score_13 = fields.Integer(string="Peace and Conflict 1")
    score_14 = fields.Integer(string="Peace and Conflict 2")
    score_15 = fields.Integer(string="Peace and Conflict 3")
    score_16 = fields.Integer(string="Intercultural Competence 1")
    score_17 = fields.Integer(string="Intercultural Competence 2")
    score_18 = fields.Integer(string="Intercultural Competence 3")

    total_score = fields.Integer(string="Total Score (out of 180)", compute="_compute_total_score", store=True)
    level = fields.Text(string="Level", compute="_compute_level", store=True)

    global_awareness_pct = fields.Float(string="Global Awareness %", compute="_compute_total_score", store=True)
    civic_participation_pct = fields.Float(string="Civic Participation %", compute="_compute_total_score", store=True)
    environment_pct = fields.Float(string="Environment %", compute="_compute_total_score", store=True)
    ethical_pct = fields.Float(string="Ethical Consumption %", compute="_compute_total_score", store=True)
    peace_pct = fields.Float(string="Peace & Conflict %", compute="_compute_total_score", store=True)
    intercultural_pct = fields.Float(string="Intercultural Competence %", compute="_compute_total_score", store=True)
    global_awareness = fields.Integer(string="Global Awareness Score", compute="_compute_total_score", store=True)
    civic_participation = fields.Integer(string="Civic Participation Score", compute="_compute_total_score", store=True)
    environment = fields.Integer(string="Environment Score", compute="_compute_total_score", store=True)
    ethical = fields.Integer(string="Ethical Consumption Score", compute="_compute_total_score", store=True)
    peace = fields.Integer(string="Peace & Conflict Score", compute="_compute_total_score", store=True)
    intercultural = fields.Integer(string="Intercultural Competence Score", compute="_compute_total_score", store=True)
    submitted_on = fields.Datetime(string="Submitted On", default=fields.Datetime.now, readonly=True)

    email_group_id = fields.Many2one(
        comodel_name='gdfh.email.group',
        string="Email Group",
        ondelete="set null"
    )

    @api.model
    def create(self, vals):
        email = vals.get('email')
        if email:
            group = self.env['gdfh.email.group'].search([('email', '=', email)], limit=1)
            if not group:
                group = self.env['gdfh.email.group'].create({'email': email})
            vals['email_group_id'] = group.id
        return super().create(vals)

    @api.depends(
        'score_1', 'score_2', 'score_3', 'score_4', 'score_5', 'score_6',
        'score_7', 'score_8', 'score_9', 'score_10', 'score_11', 'score_12',
        'score_13', 'score_14', 'score_15', 'score_16', 'score_17', 'score_18'
    )
    def _compute_total_score(self):
        for rec in self:
            group_scores = {
                'global_awareness': sum([rec.score_1 or 0, rec.score_2 or 0, rec.score_3 or 0]),
                'civic_participation': sum([rec.score_4 or 0, rec.score_5 or 0, rec.score_6 or 0]),
                'environment': sum([rec.score_7 or 0, rec.score_8 or 0, rec.score_9 or 0]),
                'ethical': sum([rec.score_10 or 0, rec.score_11 or 0, rec.score_12 or 0]),
                'peace': sum([rec.score_13 or 0, rec.score_14 or 0, rec.score_15 or 0]),
                'intercultural': sum([rec.score_16 or 0, rec.score_17 or 0, rec.score_18 or 0]),
            }
            rec.global_awareness = group_scores['global_awareness']
            rec.civic_participation = group_scores['civic_participation']
            rec.environment = group_scores['environment']
            rec.ethical = group_scores['ethical']
            rec.peace = group_scores['peace']
            rec.intercultural = group_scores['intercultural']

            max_per_group = 30.0
            rec.global_awareness_pct = round((group_scores['global_awareness'] / max_per_group) * 100)
            rec.civic_participation_pct = round((group_scores['civic_participation'] / max_per_group) * 100)
            rec.environment_pct = round((group_scores['environment'] / max_per_group) * 100)
            rec.ethical_pct = round((group_scores['ethical'] / max_per_group) * 100)
            rec.peace_pct = round((group_scores['peace'] / max_per_group) * 100)
            rec.intercultural_pct = round((group_scores['intercultural'] / max_per_group) * 100)

            rec.total_score = sum(group_scores.values())

    @api.depends('total_score')
    def _compute_level(self):
        for rec in self:
            score = rec.total_score
            if score >= 150:
                rec.level = "Progressive Visionary: Your actions profoundly align with and actively advance a progressive world. You are a significant source of positive change."
            elif score >= 120:
                rec.level = "Strong Contributor: You consistently contribute meaningfully and consciously towards a progressive world. Your efforts make a tangible difference."
            elif score >= 90:
                rec.level = "Emerging Contributor: You are on the path of contributing to a progressive world. There's significant potential to deepen your impact and explore new areas."
            else:
                rec.level = "Needs Focused Engagement: This indicates significant room for reflection, learning, and growth in actively contributing to a progressive world. Focus on foundational actions."

    def print_report(self):
        if len(self) != 1:
            raise UserError("Please select a single record to print.")
        return self.env.ref('gdfh_scoring_test.action_report_gdfh_result').report_action(self)