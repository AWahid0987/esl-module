from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # اوپر Note Sheet والی general info
    notesheet_comment = fields.Text(string="نوٹ شیٹ نوٹس")

    marital_period = fields.Char(string="عرصہ عہد")
    home_member = fields.Char(string="گھر کے کتنے افراد عهد میں ہیں؟")

    marital_period_year = fields.Integer(string="سال")
    marital_period_month = fields.Integer(string="مہینہ")
    multan = fields.Char(string="ملتان")
    additional_features = fields.Char(string="اضافی وضائف")
    which_one = fields.Char(string="کون سی")
    many_days = fields.Char(string="کتنے دن")

    martaba = fields.Char(string="مرتبہ")
    pabandi_namaz = fields.Selection(
        [("yes", "ہاں"), ("no", "نہیں")],
        string="پابندی نماز",
        default="no",
    )

    marfat = fields.Char(string="معرفت")

    kalma_taiba = fields.Selection(
        [
            ("10", "10"),
            ("1000", "1000"),

        ],
        string="کلمہ طیبہ",

    )
    la_ila_ha = fields.Selection(
        [
            ("10", "10"),
            ("1000", "1000"),

        ],
        string="لا اله الا الله",

    )
    istagfarallah = fields.Selection(
        [
            ("10", "10"),
            ("1000", "1000"),

        ],
        string="استغفر اللہ",

    )
    qaza_nemaz = fields.Selection(
        [
            ("qaza_fajr", "فجر"),
            ("qaza_zuhr", "ظہر"),
            ("qaza_asr", "عصر"),
            ("qaza_maghrib", "مغرب"),
            ("qaza_isha", "عشاء"),

        ],
        string="کون سی قضا ہوتی ہیں؟",

    )
    pay_the_fine = fields.Selection(
        [
            ("Yes", "ہاں"),
            ("No", "نہیں"),

        ],
        string=" قضا ادا کرتے ہیں؟",

    )
    religion_and_lineage = fields.Selection(
        [
            ("Yes", "ہاں"),
            ("No", "نہیں"),

        ],
        string="رعبت دین و سلسلە",

    )
    curtain = fields.Selection(
        [
            ("Yes", "ہاں"),
            ("No", "نہیں"),

        ],
        string=" شراعی پرده (خاتون)",

    )
    beard = fields.Selection(
        [
            ("Yes", "ہاں"),
            ("No", "نہیں"),

        ],
        string="داڑھی(مرد)",

    )
    quran = fields.Selection(
        [
            ("Yes", "ہاں"),
            ("No", "نہیں"),

        ],
        string=" قرآن شریف",

    )
    restrictions = fields.Selection(
        [
            ("Yes", "ہاں"),
            ("No", "نہیں"),

        ],
        string=" پابندی اشراق",

    )
    ayatul_kursi = fields.Selection(
        [
            ("03", "03"),
            ("70", "70"),

        ],
        string="آیته الکرسی",

    )
    prayer_connection = fields.Selection(
        [
            ("11", "11"),
            ("100", "100"),

        ],
        string="دعاء تعلق",

    )
    prayers = fields.Selection(
        [
            ("3", "3"),
            ("15", "15"),

        ],
        string="دعاء سواس",

    )
    allah = fields.Selection(
        [
            ("10", "10"),
            ("1000", "1000"),

        ],
        string="اللہ",

    )
    daru_pak = fields.Selection(
        [
            ("10", "10"),
            ("1000", "1000"),

        ],
        string="درود پاک",

    )

    praise_be_to_god = fields.Selection(
        [
            ("10", "10"),
            ("100", "100"),

        ],
        string="سبحان الله العظیم سبحان الله وبحمده ",

    )

    # اوپر checkbox کو yes/no option بنا دیا (selection)
    pabandi_wazaif = fields.Selection(
        [
            ("yes", "ہاں"),
            ("no", "نہیں"),
        ],
        string="پابندی وظائف",
        default="no",
    )

    # نیچے تفصیل افرادِ خانہ
    family_line_ids = fields.One2many(
        "hr.employee.family.line",
        "employee_id",
        string="تفصیل افرادِ خانہ",
    )
    pabandi_tahajjud = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string="پابندی تہجد")


class HrEmployeeFamilyLine(models.Model):
    _name = "hr.employee.family.line"
    _description = "Employee Family Detail (Notesheet)"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        ondelete="cascade",
    )

    # Basic identity columns (right side of grid)
    member_name = fields.Char(string="نام")
    relation = fields.Char(string="رشتہ")
    age = fields.Integer(string="عمر")

    marital_period = fields.Char(string="عرصہ عہد")
    marital_period_year = fields.Integer(string="سال")
    marital_period_month = fields.Integer(string="مہینہ")

    marfat = fields.Char(string="معرفت")
    occupation = fields.Char(string="روزگار")
    education = fields.Char(string="تعلیم")
    monthly_income = fields.Char(string="ماہانہ آمدن / اخراجات")
    kalma_taiba = fields.Char(string="کلمہ طیبہ")

    # ─── yes/no options (selection) ───
    shari_parda = fields.Selection(
        [("yes", "ہاں"), ("no", "نہیں")],
        string="شرعی پردہ",
        default="no",
    )
    pabandi_tahajjud = fields.Selection(
        [("yes", "ہاں"), ("no", "نہیں")],
        string="پابندی تہجد",
        default="no",
    )
    pabandi_ishraq = fields.Selection(
        [("yes", "ہاں"), ("no", "نہیں")],
        string="پابندی اشراق",
        default="no",
    )
    pabandi_namaz = fields.Selection(
        [("yes", "ہاں"), ("no", "نہیں")],
        string="پابندی نماز",
        default="no",
    )
    pabandi_wazaif = fields.Selection(
        [("yes", "ہاں"), ("no", "نہیں")],
        string="پابندی وظائف",
        default="no",
    )

    # Qaza Namaz converted into Boolean fields
    qaza_none = fields.Boolean(string="کوئی نہیں")
    qaza_fajr = fields.Boolean(string="فجر")
    qaza_zuhr = fields.Boolean(string="ظہر")
    qaza_asr = fields.Boolean(string="عصر")
    qaza_maghrib = fields.Boolean(string="مغرب")
    qaza_isha = fields.Boolean(string="عشاء")
    qaza_multiple = fields.Boolean(string="متعدد / پانچوں")
    pay_the_fine = fields.Selection(
        [
            ("Yes", "ہاں"),
            ("No", "نہیں"),

        ],
        string=" قضا ادا کرتے ہیں؟",

    )

    extra_notes = fields.Char(string="اضافی نوٹ")

    @api.onchange(
        'qaza_none',
        'qaza_fajr',
        'qaza_zuhr',
        'qaza_asr',
        'qaza_maghrib',
        'qaza_isha',
        'qaza_multiple'
    )
    def _onchange_qaza(self):
        # Ensure only one checkbox is selected if you want radio-like behavior
        fields_checked = [
            f for f in [
                self.qaza_none,
                self.qaza_fajr,
                self.qaza_zuhr,
                self.qaza_asr,
                self.qaza_maghrib,
                self.qaza_isha,
                self.qaza_multiple
            ] if f
        ]

        if len(fields_checked) > 1:
            # Reset all except the last changed (you can customize behavior)
            for f_name in [
                'qaza_none',
                'qaza_fajr',
                'qaza_zuhr',
                'qaza_asr',
                'qaza_maghrib',
                'qaza_isha',
                'qaza_multiple'
            ]:
                setattr(self, f_name, False)
