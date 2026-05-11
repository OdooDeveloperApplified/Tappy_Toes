from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class CrmLeadAPI(http.Controller):

    @http.route('/create-crm-lead', type='http', auth='public', methods=['POST'], csrf=False)
    def create_crm_lead(self, **post):
        try:
            # Accept JSON OR form-data
            data = post
            if not post:
                data = json.loads(request.httprequest.data or "{}")

            location = data.get('location')
            company = False
            if location:
                company = request.env['res.company'].sudo().search(
                    [('name', '=', location)],
                    limit=1
                )
                # ❌ Location mismatch → lead create na karo
                if not company:
                    return json.dumps({
                        'status': False,
                        'message': 'Location Mismatch'
                    })

            name = data.get('name')
            email = data.get('email')
            phone = data.get('phone')
            message = data.get('message')

            utm_source = data.get('utm_source')
            utm_medium = data.get('utm_medium')
            utm_campaign = data.get('utm_campaign')
            utm_content = data.get('utm_content')
            utm_term = data.get('utm_term')

            landing_page_url = data.get('landing_page_url')
            gclid = data.get('gclid')
            fbclid = data.get('fbclid')
            ttclid = data.get('ttclid')
            lead_source = data.get('lead_source')  # website / meta / google / tiktok

            if not name:
                return json.dumps({
                    'status': False,
                    'message': 'Name is required'
                })
            
            # ❌ Location required
            if not location:
                return json.dumps({
                    'status': False,
                    'message': 'Location is required'
                })

            lead = request.env['crm.lead'].sudo().create({
                'name': name,
                'email_from': email,
                'phone': phone,
                'location_name': company.id if company else False,
                'company_id':company.id,
                'user_id': False,
                'description': message,
                'utm_source': utm_source,
                'utm_medium': utm_medium,
                'utm_campaign': utm_campaign,
                'utm_content': utm_content,
                'utm_term': utm_term,
                'landing_page_url': landing_page_url,
                'gclid': gclid,
                'fbclid': fbclid,
                'ttclid': ttclid,
                'lead_source': lead_source,
                'campaign_id': False,
                'source_id': False,
                'medium_id': False,
                'type': 'lead',
            })

            _logger.info("CRM Lead Created ID: %s", lead.id)
            _logger.info("CRM Lead Created Read: %s", lead.read())

            return json.dumps({
                'status': True,
                'lead_id': lead.id,
                'message': 'CRM Lead created successfully'
            })

        except Exception as e:
            _logger.exception("Error creating CRM Lead")
            return json.dumps({
                'status': False,
                'error': str(e)
            })

    # @http.route('/create-crm-lead', type='http', auth='public', methods=['POST'], csrf=False)
    # def create_crm_lead(self, **post):
    #     try:
    #         # Accept JSON OR form-data
    #         data = post
    #         if not post:
    #             data = json.loads(request.httprequest.data or "{}")
            
    #         location = data.get('location')
    #         company = False
    #         if location:
    #             company = request.env['res.company'].sudo().search(
    #                 [('name', '=', location)],
    #                 limit=1
    #             )
    #         name = data.get('name')
    #         email = data.get('email')
    #         phone = data.get('phone')
    #         message = data.get('message')
    #         utm_source = data.get('utm_source')
    #         utm_medium = data.get('utm_medium')
    #         utm_campaign = data.get('utm_campaign')
    #         utm_content = data.get('utm_content')
    #         utm_term = data.get('utm_term')
    #         landing_page_url = data.get('landing_page_url')
    #         gclid = data.get('gclid')
    #         fbclid = data.get('fbclid')
    #         ttclid = data.get('ttclid')
    #         lead_source = data.get('lead_source')  # website / meta / google / tiktok

    #         if not name:
    #             return json.dumps({
    #                 'status': False,
    #                 'message': 'Name is required'
    #             })

    #         lead = request.env['crm.lead'].sudo().create({
    #             'name': name,
    #             'email_from': email,
    #             'phone': phone,
    #             'location_name': company.id if company else False,
    #             'description': message,
    #             'utm_source': utm_source,
    #             'utm_medium': utm_medium,
    #             'utm_campaign': utm_campaign,
    #             'utm_content': utm_content,
    #             'utm_term': utm_term,
    #             'landing_page_url': landing_page_url,
    #             'gclid': gclid,
    #             'fbclid': fbclid,
    #             'ttclid': ttclid,
    #             'lead_source': lead_source,
    #             'type': 'lead',
    #         })

    #         _logger.info("CRM Lead Created ID: %s", lead.id)

    #         return json.dumps({
    #             'status': True,
    #             'lead_id': lead.id,
    #             'message': 'CRM Lead created successfully'
    #         })

    #     except Exception as e:
    #         _logger.exception("Error creating CRM Lead")
    #         return json.dumps({
    #             'status': False,
    #             'error': str(e)
    #         })



    ##################### MY CODE TO RESOLVE THE UTM MAPPING ISSUE (KEEP): starts #####################
    # @http.route('/create-crm-lead', type='http', auth='public', methods=['POST'], csrf=False)
    # def create_crm_lead(self, **post):
    #     try:
    #         # Accept JSON OR form-data
    #         data = post if post else json.loads(request.httprequest.data or "{}")

    #         # -------------------------------
    #         # Location Handling
    #         # -------------------------------
    #         location = data.get('location')
    #         company = False

    #         if not location:
    #             return json.dumps({'status': False, 'message': 'Location is required'})

    #         company = request.env['res.company'].sudo().search(
    #             [('name', '=', location)], limit=1
    #         )

    #         if not company:
    #             return json.dumps({'status': False, 'message': 'Location Mismatch'})

    #         # -------------------------------
    #         # Basic Fields
    #         # -------------------------------
    #         name = data.get('name')
    #         email = data.get('email')
    #         phone = data.get('phone')
    #         message = data.get('message')

    #         if not name:
    #             return json.dumps({'status': False, 'message': 'Name is required'})

    #         # -------------------------------
    #         # Tracking Fields
    #         # -------------------------------
    #         utm_source = data.get('utm_source')
    #         utm_medium = data.get('utm_medium')
    #         utm_campaign = data.get('utm_campaign')

    #         utm_content = data.get('utm_content')
    #         utm_term = data.get('utm_term')

    #         landing_page_url = data.get('landing_page_url')
    #         gclid = data.get('gclid')
    #         fbclid = data.get('fbclid')
    #         ttclid = data.get('ttclid')

    #         lead_source = data.get('lead_source')

    #         # Fallback if UTM missing
    #         if not utm_source:
    #             utm_source = lead_source

    #         # -------------------------------
    #         # Log incoming tracking data
    #         # -------------------------------
    #         _logger.info("Incoming UTM Data: %s", {
    #             'utm_source': utm_source,
    #             'utm_medium': utm_medium,
    #             'utm_campaign': utm_campaign,
    #             'gclid': gclid,
    #             'fbclid': fbclid,
    #             'ttclid': ttclid
    #         })

    #         # -------------------------------
    #         # Map to Odoo UTM Models
    #         # -------------------------------
    #         source = False
    #         medium = False
    #         campaign = False

    #         if utm_source:
    #             source = request.env['utm.source'].sudo().search(
    #                 [('name', '=', utm_source)], limit=1
    #             ) or request.env['utm.source'].sudo().create({'name': utm_source})

    #         if utm_medium:
    #             medium = request.env['utm.medium'].sudo().search(
    #                 [('name', '=', utm_medium)], limit=1
    #             ) or request.env['utm.medium'].sudo().create({'name': utm_medium})

    #         if utm_campaign:
    #             campaign = request.env['utm.campaign'].sudo().search(
    #                 [('name', '=', utm_campaign)], limit=1
    #             ) or request.env['utm.campaign'].sudo().create({'name': utm_campaign})

    #         # -------------------------------
    #         # Create Lead
    #         # -------------------------------
    #         lead_vals = {
    #             'name': name,
    #             'email_from': email,
    #             'phone': phone,
    #             'description': message,
    #             'location_name': company.id,
    #             'company_id': company.id,
    #             'type': 'lead',

    #             # ✅ Odoo native tracking
    #             'source_id': source.id if source else False,
    #             'medium_id': medium.id if medium else False,
    #             'campaign_id': campaign.id if campaign else False,

    #             # ✅ Your custom fields (kept)
    #             'utm_source': utm_source,
    #             'utm_medium': utm_medium,
    #             'utm_campaign': utm_campaign,
    #             'utm_content': utm_content,
    #             'utm_term': utm_term,

    #             'landing_page_url': landing_page_url,
    #             'gclid': gclid,
    #             'fbclid': fbclid,
    #             'ttclid': ttclid,
    #             'lead_source': lead_source,
    #         }

    #         lead = request.env['crm.lead'].sudo().create(lead_vals)

    #         _logger.info("CRM Lead Created ID: %s", lead.id)

    #         return json.dumps({
    #             'status': True,
    #             'lead_id': lead.id,
    #             'message': 'CRM Lead created successfully'
    #         })

    #     except Exception as e:
    #         _logger.exception("Error creating CRM Lead")
    #         return json.dumps({
    #             'status': False,
    #             'error': str(e)
    #         })
    ##################### MY CODE TO RESOLVE THE UTM MAPPING ISSUE (KEEP): ends #####################