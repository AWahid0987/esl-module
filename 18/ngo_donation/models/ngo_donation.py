from odoo import models, fields
import requests
import logging
import re

_logger = logging.getLogger(__name__)


class NGODonation(models.Model):
    _name = "ngo.donation"
    _description = "Donation"

    donor_id = fields.Many2one("res.partner", required=True, ondelete="cascade")
    project_id = fields.Many2one("project.project", required=True, ondelete="cascade")
    date = fields.Date(default=fields.Date.today)
    amount = fields.Monetary(required=True)
    currency_id = fields.Many2one("res.currency", required=True, default=lambda self: self.env.company.currency_id)
    payment_status = fields.Selection(
        [("pending", "Pending"), ("paid", "Paid"), ("cancelled", "Cancelled")], default="pending", required=True
    )
    payment_reference = fields.Char()
    notes = fields.Text()


class Website(models.Model):
    _inherit = 'website'
    
    def translate_text(self, text, target_lang='en'):
        """
        Translate text using free translation API
        Falls back to MyMemory API if LibreTranslate fails
        Strips HTML tags before translating to avoid translation issues
        """
        if not text or target_lang == 'en_US' or target_lang.startswith('en'):
            return text
        
        # Strip HTML tags from text before translating
        # This prevents translation APIs from including HTML tags in translated text
        text_without_html = re.sub(r'<[^>]+>', '', text)
        # Clean up extra whitespace
        text_without_html = ' '.join(text_without_html.split())
        
        if not text_without_html:
            return text
        
        # Map Odoo language codes to translation API language codes
        lang_map = {
            'de_DE': 'de',
            'de': 'de',
            'fr_FR': 'fr',
            'fr': 'fr',
            'es_ES': 'es',
            'es': 'es',
            'it_IT': 'it',
            'it': 'it',
            'pt_PT': 'pt',
            'pt': 'pt',
            'nl_NL': 'nl',
            'nl': 'nl',
            'pl_PL': 'pl',
            'pl': 'pl',
            'ru_RU': 'ru',
            'ru': 'ru',
            'zh_CN': 'zh',
            'zh': 'zh',
            'ja_JP': 'ja',
            'ja': 'ja',
            'ar': 'ar',
            'hi_IN': 'hi',
            'hi': 'hi',
        }
        
        # Extract language code
        lang_code = target_lang.split('_')[0] if '_' in target_lang else target_lang
        target_lang_code = lang_map.get(lang_code, lang_code)
        
        if target_lang_code == 'en':
            return text
        
        # Try MyMemory Translation API first (more reliable, free, no API key required)
        try:
            mymemory_url = "https://api.mymemory.translated.net/get"
            params = {
                'q': text_without_html,
                'langpair': f'en|{target_lang_code}'
            }
            
            response = requests.get(mymemory_url, params=params, timeout=5)
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('responseData', {}).get('translatedText'):
                        translated = result['responseData']['translatedText']
                        # MyMemory sometimes returns "MYMEMORY WARNING" - filter it out
                        if 'MYMEMORY WARNING' not in translated:
                            return translated
                except (ValueError, KeyError) as e:
                    _logger.debug(f"MyMemory JSON parse failed: {e}")
        except Exception as e:
            _logger.debug(f"MyMemory Translation failed: {e}")
        
        # Fallback to LibreTranslate API
        try:
            libre_url = "https://libretranslate.de/translate"
            headers = {
                'Content-Type': 'application/json',
            }
            payload = {
                'q': text_without_html,
                'source': 'en',
                'target': target_lang_code,
                'format': 'text'
            }
            
            response = requests.post(libre_url, json=payload, headers=headers, timeout=5)
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('translatedText'):
                        return result['translatedText']
                except ValueError as e:
                    _logger.debug(f"LibreTranslate JSON parse failed: {e}, Response: {response.text[:100]}")
        except Exception as e:
            _logger.debug(f"LibreTranslate failed: {e}")
        
        # If all APIs fail, return original text (without HTML tags if translation was attempted)
        return text_without_html if text_without_html != text else text
    
    def get_donation_translations(self):
        """Get translated donation strings using external translation API"""
        # Get current language from context
        lang = self.env.context.get('lang') or self.env.user.lang or 'en_US'
        
        # English source texts
        texts = {
            'donation_amount_label': 'Donation Amount:',
            'donation_amount_help': 'Enter any amount',
            'thank_you_donation': 'Thank you for your donation.',
            'donation': 'Donation',
            'donation_summary': 'Donation summary',
        }
        
        # Translate each text
        translated = {}
        for key, text in texts.items():
            translated[key] = self.translate_text(text, lang)
        
        return translated
    
    def translate_product(self, product):
        """Translate product name and description using external translation API"""
        if not product:
            return {'name': '', 'description': '', 'description_sale': ''}
        
        try:
            lang = self.env.context.get('lang') or self.env.user.lang or 'en_US'
            
            # Get product name and translate
            product_name = product.name or ''
            if not product_name:
                return {'name': '', 'description': '', 'description_sale': ''}
            
            translated_name = self.translate_text(product_name, lang) if product_name else product_name
            
            # Get product description (prefer description_ecommerce, then description_sale, then description)
            product_description = product.description_ecommerce or product.description_sale or product.description or ''
            translated_description = self.translate_text(product_description, lang) if product_description else product_description
            
            # Get description_sale separately if it exists
            description_sale = product.description_sale or ''
            translated_description_sale = self.translate_text(description_sale, lang) if description_sale else description_sale
            
            return {
                'name': translated_name or product_name,
                'description': translated_description or product_description,
                'description_sale': translated_description_sale or description_sale,
            }
        except Exception as e:
            _logger.warning(f"Error translating product {product.id if product else 'None'}: {e}")
            # Return original values on error
            return {
                'name': product.name if product else '',
                'description': product.description_ecommerce or product.description_sale or product.description if product else '',
                'description_sale': product.description_sale if product else '',
            }
