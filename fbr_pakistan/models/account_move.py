from odoo import models, fields, api, tools
from odoo.tools import date_utils
import requests
import json
from datetime import datetime
from markupsafe import Markup
import qrcode
import io
import base64


class Account_move(models.Model):
    _inherit = "account.move"

    fbr_response = fields.Text(string="FBR Response", readonly=False)
    fbr_sent = fields.Boolean(string="Sent to FBR", default=False)
    payload = fields.Text(
        string="Payload", help="JSON payload sent to FBR"
    )
    fbr_qr_code = fields.Image(
        string="FBR QR Code",
        help="QR code generated from FBR invoice number"
    )
    fbr_invoice_number = fields.Char(
        string="FBR Invoice Number",
        help="Invoice number as required by FBR"
    )
    fbr_digital_invoice_logo = fields.Image(
        string="FBR Digital Invoice Logo",
        help="FBR Digital Invoice logo",
        readonly=True,
        default=lambda self: self._get_default_fbr_logo()
    )

    fbr_document_type_id = fields.Many2one(
        "fbr.document.type",
        string="FBR Document Type",
        help="Select the FBR document type",
    )

    fbr_sale_type_id = fields.Many2one(
        "fbr.sale.type", string="FBR Sale Type", help="Select the FBR sale type"
    )

    fbr_scenario_id = fields.Many2one(
        "fbr.scenarios", string="FBR Scenario", help="Select the FBR scenario code"
    )

    fbr_reason_id = fields.Many2one(
        "fbr.reason",
        string="FBR Reason",
        help="Select the reason for return/credit note (if applicable)",
    )

    fbr_province_id = fields.Many2one(
        "fbr.province", string="FBR Province", help="Select the FBR province"
    )

    @api.model
    def _get_default_fbr_logo(self):
        image = False
        img_path = tools.misc.file_path("fbr_pakistan/static/description/di.png")
        if img_path:
            with open(img_path, "rb") as f:
                image = f.read()
        return base64.b64encode(image)


    def action_dynamic_payload(self):
        """Generate dynamic payload for FBR"""
        self.ensure_one()
        self.payload = json.dumps(self._prepare_fbr_data(), indent=2)

    def action_send_to_fbr(self):
        """Send invoice data to FBR"""
        self.ensure_one()

        # Prepare the data
        invoice_data = self._prepare_fbr_data()
        self.payload = json.dumps(invoice_data, indent=2)

        # FBR API configuration
        url = self.env["ir.config_parameter"].sudo().get_param("fbr.api.url", "")
        token = self.env["ir.config_parameter"].sudo().get_param("fbr.api.token", "")

        if not token or not url:
            return self._show_notification(
                "FBR API token not configured. Please set 'fbr.api.token' in system parameters.",
                "danger",
            )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Odoo/17.0",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
        }

        try:
            response = requests.post(
                url=url, headers=headers, data=json.dumps(invoice_data), timeout=30
            )

            # Update FBR fields
            self.write(
                {
                    "fbr_response": response.text,
                    "fbr_sent": True if response.status_code == 200 else False,
                }
            )

            # Create success/failure message for chatter
            if response.status_code == 200:
                self._process_fbr_success_response(response)
                self._post_fbr_success_message(response)
                return self._show_success_notification_with_reload()
            else:
                self._post_fbr_error_message(response)
                return self._show_error_notification(response)

        except requests.exceptions.Timeout:
            error_msg = "FBR API request timed out. Please try again."
            self._post_fbr_timeout_message()
            return self._show_notification(error_msg, "warning")

        except requests.exceptions.ConnectionError:
            error_msg = (
                "Could not connect to FBR API. Please check your internet connection."
            )
            self._post_fbr_connection_error_message()
            return self._show_notification(error_msg, "danger")

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self._post_fbr_exception_message(str(e))
            return self._show_notification(error_msg, "danger")

    def _post_fbr_success_message(self, response):
        """Post success message to chatter"""
        success_message = Markup(
            f"""
        <div class="alert alert-success border-0 shadow-sm" role="alert">
            <div class="d-flex align-items-center mb-3">
                <div class="flex-shrink-0">
                    <i class="fa fa-check-circle fa-2x text-success"></i>
                </div>
                <div class="flex-grow-1 ms-3">
                    <h5 class="alert-heading mb-1">
                        <i class="fa fa-paper-plane me-2"></i>Successfully Sent to FBR
                    </h5>
                    <p class="mb-0 text-muted">Invoice data has been successfully submitted to Pakistan FBR system.</p>
                </div>
            </div>

            <div class="row g-2 mb-3">
                <div class="col-md-4">
                    <div class="d-flex align-items-center">
                        <i class="fa fa-calendar-check me-2 text-success"></i>
                        <div>
                            <small class="text-muted d-block">Submission Time</small>
                            <strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="d-flex align-items-center">
                        <i class="fa fa-info-circle me-2 text-success"></i>
                        <div>
                            <small class="text-muted d-block">Status Code</small>
                            <strong>{response.status_code}</strong>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="d-flex align-items-center">
                        <i class="fa fa-file-invoice me-2 text-success"></i>
                        <div>
                            <small class="text-muted d-block">Invoice</small>
                            <strong>{self.name}</strong>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-light rounded p-3">
                <h6 class="mb-2">
                    <i class="fa fa-server me-2"></i>FBR Response
                </h6>
                <pre class="mb-0 small text-wrap" style="white-space: pre-wrap; word-break: break-word; max-height: 200px; overflow-y: auto;">{response.text}</pre>
            </div>
        </div>
        """
        )

        self.message_post(
            body=success_message,
            subject="FBR Submission Successful",
            message_type="comment",
        )

    def _post_fbr_error_message(self, response):
        """Post error message to chatter"""
        error_message = Markup(
            f"""
        <div class="alert alert-danger border-0 shadow-sm" role="alert">
            <div class="d-flex align-items-center mb-3">
                <div class="flex-shrink-0">
                    <i class="fa fa-exclamation-triangle fa-2x text-danger"></i>
                </div>
                <div class="flex-grow-1 ms-3">
                    <h5 class="alert-heading mb-1">
                        <i class="fa fa-times-circle me-2"></i>FBR Submission Failed
                    </h5>
                    <p class="mb-0">There was an error submitting the invoice to FBR. Please review and try again.</p>
                </div>
            </div>

            <div class="row g-2 mb-3">
                <div class="col-md-4">
                    <div class="d-flex align-items-center">
                        <i class="fa fa-calendar-times me-2 text-danger"></i>
                        <div>
                            <small class="text-muted d-block">Failed At</small>
                            <strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="d-flex align-items-center">
                        <i class="fa fa-exclamation-circle me-2 text-danger"></i>
                        <div>
                            <small class="text-muted d-block">Status Code</small>
                            <strong>{response.status_code}</strong>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="d-flex align-items-center">
                        <i class="fa fa-file-invoice me-2 text-danger"></i>
                        <div>
                            <small class="text-muted d-block">Invoice</small>
                            <strong>{self.name}</strong>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-light rounded p-3">
                <h6 class="mb-2 text-danger">
                    <i class="fa fa-bug me-2"></i>Error Details
                </h6>
                <pre class="mb-0 small text-wrap text-danger" style="white-space: pre-wrap; word-break: break-word; max-height: 200px; overflow-y: auto;">{response.text}</pre>
            </div>
        </div>
        """
        )

        self.message_post(
            body=error_message, subject="FBR Submission Failed", message_type="comment"
        )

    def _post_fbr_timeout_message(self):
        """Post timeout message to chatter"""
        timeout_message = Markup(
            f"""
        <div class="alert alert-warning border-0 shadow-sm" role="alert">
            <div class="d-flex align-items-center">
                <div class="flex-shrink-0">
                    <i class="fa fa-hourglass-end fa-2x text-warning"></i>
                </div>
                <div class="flex-grow-1 ms-3">
                    <h5 class="alert-heading mb-1">
                        <i class="fa fa-spinner me-2"></i>FBR Submission Timeout
                    </h5>
                    <p class="mb-2">The request to FBR API timed out. This might be due to network issues or high server load.</p>
                    <small class="text-muted">
                        <i class="fa fa-info-circle me-1"></i>
                        Attempted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Invoice: {self.name}
                    </small>
                </div>
            </div>
        </div>
        """
        )

        self.message_post(
            body=timeout_message,
            subject="FBR Submission Timeout",
            message_type="comment",
        )

    def _post_fbr_connection_error_message(self):
        """Post connection error message to chatter"""
        connection_message = Markup(
            f"""
        <div class="alert alert-danger border-0 shadow-sm" role="alert">
            <div class="d-flex align-items-center">
                <div class="flex-shrink-0">
                    <i class="fa fa-wifi fa-2x text-danger"></i>
                </div>
                <div class="flex-grow-1 ms-3">
                    <h5 class="alert-heading mb-1">
                        <i class="fa fa-unlink me-2"></i>FBR Connection Failed
                    </h5>
                    <p class="mb-2">Could not establish connection to FBR API. Please check your internet connection and try again.</p>
                    <small class="text-muted">
                        <i class="fa fa-info-circle me-1"></i>
                        Attempted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Invoice: {self.name}
                    </small>
                </div>
            </div>
        </div>
        """
        )

        self.message_post(
            body=connection_message,
            subject="FBR Connection Error",
            message_type="comment",
        )

    def _post_fbr_exception_message(self, error_details):
        """Post exception message to chatter"""
        exception_message = Markup(
            f"""
        <div class="alert alert-danger border-0 shadow-sm" role="alert">
            <div class="d-flex align-items-center mb-3">
                <div class="flex-shrink-0">
                    <i class="fa fa-bug fa-2x text-danger"></i>
                </div>
                <div class="flex-grow-1 ms-3">
                    <h5 class="alert-heading mb-1">
                        <i class="fa fa-exclamation-triangle me-2"></i>FBR System Error
                    </h5>
                    <p class="mb-0">An unexpected error occurred while processing the FBR submission.</p>
                </div>
            </div>

            <div class="bg-light rounded p-3">
                <h6 class="mb-2 text-danger">
                    <i class="fa fa-code me-2"></i>Technical Details
                </h6>
                <pre class="mb-0 small text-wrap text-danger" style="white-space: pre-wrap; word-break: break-word;">{error_details}</pre>
                <small class="text-muted d-block mt-2">
                    <i class="fa fa-info-circle me-1"></i>
                    Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Invoice: {self.name}
                </small>
            </div>
        </div>
        """
        )

        self.message_post(
            body=exception_message, subject="FBR System Error", message_type="comment"
        )

    def _show_success_notification_with_reload(self):
        """Show success notification and soft reload"""
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "FBR Integration Success",
                "message": "Invoice successfully sent to FBR! Check chatter for details.",
                "type": "success",
                "sticky": False,
                "next": {
                    "type": "ir.actions.client",
                    "tag": "reload",
                },
            },
        }

    def _show_error_notification(self, response):
        """Show error notification"""
        if response.status_code == 403:
            message = "Authentication failed. Please verify your FBR token."
        elif response.status_code == 401:
            message = "Invalid or expired token. Please update your FBR token."
        else:
            message = f"Failed to send to FBR (Status: {response.status_code}). Check chatter for details."

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "FBR Integration Failed",
                "message": message,
                "type": "danger",
                "sticky": True,
            },
        }

    def _prepare_fbr_data(self):
        """Prepare invoice data in FBR format"""
        self.ensure_one()
        company = self.company_id
        partner = self.partner_id

        return {
            "invoiceType": (
                self.fbr_document_type_id.name if self.fbr_document_type_id else ""
            ),
            "invoiceDate": (
                self.invoice_date.strftime("%Y-%m-%d")
                if self.invoice_date
                else self.date.strftime("%Y-%m-%d")
            ),
            "sellerNTNCNIC": company.vat or "",
            "sellerBusinessName": company.name,
            "sellerProvince": self.fbr_province_id.name if self.fbr_province_id else "",
            "sellerAddress": company.street or "",
            "buyerNTNCNIC": partner.vat or "",
            "buyerBusinessName": partner.name,
            "buyerProvince": partner.state_id.name or "",
            "buyerAddress": partner.street or "",
            "invoiceRefNo": self.name,
            "buyerRegistrationType": (
                partner.fbr_buyer_type_id.name if partner.fbr_buyer_type_id else ""
            ),
            "scenarioId": self.fbr_scenario_id.code if self.fbr_scenario_id else "",
            "reasonForReturn": self.fbr_reason_id.name if self.fbr_reason_id else "",
            "items": [
                {
                    "hsCode": line.product_id.fbr_hs_code or "",
                    "productDescription": line.name or line.product_id.name,
                    "rate": (
                        "{:.0f}%".format(line.tax_ids.amount)
                        if line.tax_ids
                        else "0.00%"
                    ),
                    "uoM": (
                        line.product_id.fbr_uom_id.name
                        if line.product_id.fbr_uom_id
                        else ""
                    ),
                    "quantity": line.quantity,
                    "totalValues": line.price_total,
                    "valueSalesExcludingST": str(line.price_subtotal),
                    "salesTaxApplicable": "{:.2f}".format(line.price_total - line.price_subtotal),
                    "fixedNotifiedValueOrRetailPrice": line.product_id.fbr_fixed_notified_value
                    or "0",
                    "salesTaxWithheldAtSource": line.product_id.fbr_sales_tax_withheld
                    or "0",
                    "extraTax": line.product_id.fbr_extra_tax or "0.00",
                    "furtherTax": line.product_id.fbr_further_tax or "0",
                    "sroScheduleNo": (
                        line.product_id.fbr_sro_id.name
                        if line.product_id.fbr_sro_id
                        else ""
                    ),
                    "fedPayable": line.product_id.fbr_fed_payable or "0",
                    "discount": line.discount,
                    "saleType": (
                        self.fbr_sale_type_id.name if self.fbr_sale_type_id else ""
                    ),
                    "sroItemSerialNo": (
                        line.product_id.fbr_sro_item_serial_id.name
                        if line.product_id.fbr_sro_item_serial_id
                        else ""
                    ),
                }
                for line in self.invoice_line_ids.filtered(
                    lambda l: l.display_type not in ["line_section", "line_note"]
                )
            ],
        }

    def _show_notification(self, message, type="info"):
        """Helper method to show notifications"""
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": message,
                "type": type,
                "sticky": type == "danger",
            },
        }

    def action_test_fbr_messages(self):
        """Test all FBR message types at once"""
        self.ensure_one()

        # Create mock response objects for testing
        class MockResponse:
            def __init__(self, status_code, text):
                self.status_code = status_code
                self.text = text

        # Test Success Message
        success_response = MockResponse(
            200,
            '{"status": "success", "invoice_id": "12345", "message": "Invoice successfully submitted to FBR"}',
        )
        self._post_fbr_success_message(success_response)

        # Test Error Message
        error_response = MockResponse(
            400,
            '{"error": "Invalid invoice data", "details": "Missing required field: buyer_ntn"}',
        )
        self._post_fbr_error_message(error_response)

        # Test Timeout Message
        self._post_fbr_timeout_message()

        # Test Connection Error Message
        self._post_fbr_connection_error_message()

        # Test Exception Message
        self._post_fbr_exception_message(
            "ValueError: Invalid JSON format in API response"
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "FBR Message Test Complete",
                "message": "All FBR message types have been posted to the chatter. Check the message log below.",
                "type": "success",
                "sticky": False,
                "next": {
                    "type": "ir.actions.client",
                    "tag": "soft_reload",
                },
            },
        }


    def _process_fbr_success_response(self, response):
        """Process successful FBR response and extract invoice number"""
        try:
            response_data = json.loads(response.text)

            # Extract invoice number
            invoice_number = response_data.get('invoiceNumber', '')

            if invoice_number:
                # Generate QR code
                qr_code_data = self._generate_fbr_qr_code(invoice_number)

                # Update fields
                self.write({
                    'fbr_invoice_number': invoice_number,
                    'fbr_qr_code': qr_code_data if qr_code_data else False,
                })

        except (json.JSONDecodeError, KeyError) as e:
            # Log error but don't fail the main process
            self.message_post(
                body=f"Warning: Could not extract invoice number from FBR response: {str(e)}",
                message_type="comment"
            )

    def _generate_fbr_qr_code(self, data):
        """Generate QR code from given data"""
        try:
            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )

            # Add data and generate QR code
            qr.add_data(data)
            qr.make(fit=True)

            # Create QR code image
            qr_image = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64 for storage
            buffer = io.BytesIO()
            qr_image.save(buffer, format='PNG')
            qr_code_data = base64.b64encode(buffer.getvalue())

            return qr_code_data

        except Exception as e:
            self.message_post(
                body=f"Error generating QR code: {str(e)}",
                message_type="comment"
            )
            return False

    def action_generate_fbr_qr_code(self):
        """Manual action to generate QR code from FBR invoice number"""
        self.ensure_one()

        if not self.fbr_invoice_number:
            return self._show_notification(
                "No FBR invoice number found. Please send to FBR first.",
                "warning"
            )

        qr_code_data = self._generate_fbr_qr_code(self.fbr_invoice_number)

        if qr_code_data:
            self.fbr_qr_code = qr_code_data
            return self._show_notification(
                "QR code generated successfully!",
                "success"
            )
        else:
            return self._show_notification(
                "Failed to generate QR code.",
                "danger"
            )