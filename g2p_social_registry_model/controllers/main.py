import logging
import base64
import requests
from datetime import datetime, date

from odoo import http, fields
from odoo.http import request

from odoo.addons.g2p_registration_portal_base.controllers.main import G2PregistrationPortalBase

_logger = logging.getLogger(__name__)


class G2PSocialRegistryModel(G2PregistrationPortalBase):
    @http.route("/portal/registration/zan_id_lookup", type="json", auth="user", csrf=False)
    def zan_id_lookup(self, zan_id):
        if not zan_id:
            return {"status": "ERROR", "message": "Zan ID is required"}

        # 1. Check in database
        id_type = request.env["g2p.id.type"].sudo().search([("name", "=", "Zanzibar ID")], limit=1)
        if not id_type:
            return {"status": "ERROR", "message": "Zanzibar ID type not found in system"}

        reg_id = (
            request.env["g2p.reg.id"]
            .sudo()
            .search([("id_type", "=", id_type.id), ("value", "=", zan_id.strip())], limit=1)
        )

        if reg_id and reg_id.partner_id:
            return {
                "status": "ALREADY_EXISTS",
                "message": "Beneficiary with this Zan ID already exists in the system."
            }

        # 2. Call Mock API
        try:
            #response = requests.get("https://mocki.io/v1/78b26feb-48cd-47bf-bf52-70129f35d549", timeout=10) #age less than 69
            response = requests.get("https://mocki.io/v1/0b022420-8bd4-4227-8456-4132a6a1e298", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "SUCCESS":
                    # For mock purpose, we assume the API returns the data for the requested ID
                    if "gender" in data:
                        data["gender"] = data["gender"].lower()

                    # Age Validation
                    dob_str = data.get("dob")
                    if dob_str:
                        try:
                            # Try parsing YYYY-MM-DD
                            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
                        except ValueError:
                            try:
                                # Try parsing DD-MM-YYYY
                                dob = datetime.strptime(dob_str, "%d-%m-%Y").date()
                            except ValueError:
                                dob = None
                        
                        if dob:
                            today = date.today()
                            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                            if age < 69:
                                return {
                                    "status": "NOT_ELIGIBLE", 
                                    "message": f"Not eligible for the pension program. Age is {age}, but must be 69+."
                                }

                    return data
                else:
                    return {"status": "NOT_FOUND", "message": "Zan ID not found in external registry"}
            else:
                return {"status": "ERROR", "message": f"External API error: {response.status_code}"}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    @http.route("/portal/registration/nominee_zan_id_lookup", type="json", auth="user", csrf=False)
    def nominee_zan_id_lookup(self, nominee_zanid):
        if not nominee_zanid:
            return {"status": "ERROR", "message": "Zan ID is required"}

        # 1. Check in database
        id_type = request.env["g2p.id.type"].sudo().search([("name", "=", "Nominee Zanzibar ID")], limit=1)
        
        if id_type:
            reg_id = (
                request.env["g2p.reg.id"]
                .sudo()
                .search([("id_type", "=", id_type.id), ("value", "=", nominee_zanid.strip())], limit=1)
            )

            if reg_id and reg_id.partner_id:
                p = reg_id.partner_id
                # Prepare data from existing partner
                data = {
                    "status": "ALREADY_EXISTS_BUT_FILL",
                    "message": "Nominee already exists in the system.",
                    "nominee_first_name": p.given_name or "",
                    "nominee_last_name": p.family_name or "",
                    # Map Gender (System uses 'male'/'female', check standard)
                    "nominee_gender": p.gender or "", 
                    "nominee_mobile": p.phone or "",
                    # Address mapping - assuming simple mapping for now
                    "nominee_house_street": p.street or "",
                    "nominee_shehia": p.street2 or "",
                     # Region/District need codes or IDs? The frontend expects values that match the select options (usually IDs or Codes).
                     # In main.py individual_update, we see p.region.id is used.
                     # But in the frontend JS, it sets values.
                     # Let's send both or send what works. The prev mock API sent Codes probably?
                     # Mock API returned "region": "MJ", "district": "mjini" (codes).
                     # So we should send Codes if possible.
                    "nominee_region": p.region.code if p.region else "",
                    "nominee_district": p.district.code if p.district else "",
                    "nominee_rel_benf": p.nominee_rel_benf or "",
                }
                return data

        # 2. Call Mock API
        try:
            response = requests.get("https://mocki.io/v1/4661e182-00d4-4f26-a450-e4e96a7cc075", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "SUCCESS":
                    # Map Mock API fields to Nominee Fields
                    # Mock: firstname, lastname, gender, mobile, street, street2...
                    mapped_data = {
                        "status": "SUCCESS",
                        "message": "Found!",
                        "nominee_first_name": data.get("firstname", ""),
                        "nominee_last_name": data.get("lastname", ""),
                        "nominee_gender": data.get("gender", "").lower(),
                        "nominee_mobile": data.get("mobile", ""),
                        "nominee_house_street": data.get("street", ""),
                        "nominee_shehia": data.get("street2", ""),
                        "nominee_rel_benf": data.get("relationship", ""),
                        # Mock API might return 'region'/'district' keys.
                        "nominee_region": data.get("region", ""),
                        "nominee_district": data.get("district", ""),
                    }
                    return mapped_data
                else:
                    return {"status": "NOT_FOUND", "message": "Nominee Zan ID not found in external registry"}
            else:
                return {"status": "ERROR", "message": f"External API error: {response.status_code}"}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    @http.route(
        ["/portal/registration/group/create/submit"],
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def group_create_submit(self, **kw):
        try:
            head_name = kw.get("name")
            beneficiary_id = None

            additional_data = {
                "name": head_name,
                "birthdate": kw.get("birthdate"),
                "gender": kw.get("gender"),
                "email": kw.get("email"),
                "address": kw.get("address"),
                # Social Status Information
                "num_preg_lact_women": int(kw.get("num_preg_lact_women", 0))
                if kw.get("num_preg_lact_women")
                else 0,
                "num_malnourished_children": int(kw.get("num_malnourished_children", 0))
                if kw.get("num_malnourished_children")
                else 0,
                "num_disabled": int(kw.get("num_disabled", 0)) if kw.get("num_disabled") else 0,
                "type_of_disability": kw.get("type_of_disability"),
                # Economic Status Information
                "caste_ethnic_group": kw.get("caste_ethnic_group"),
                "belong_to_protected_groups": kw.get("belong_to_protected_groups"),
                "other_vulnerable_status": kw.get("other_vulnerable_status"),
                "income_sources": kw.get("income_sources"),
                "annual_income": kw.get("annual_income", False),
                "owns_two_wheeler": kw.get("owns_two_wheeler"),
                "owns_three_wheeler": kw.get("owns_three_wheeler"),
                "owns_four_wheeler": kw.get("owns_four_wheeler"),
                "owns_cart": kw.get("owns_cart"),
                "land_ownership": kw.get("land_ownership"),
                "type_of_land_owned": kw.get("type_of_land_owned"),
                "land_size": float(kw.get("land_size", 0.0)) if kw.get("land_size") else 0.0,
                "owns_house": kw.get("owns_house"),
                "owns_livestock": kw.get("owns_livestock"),
            }

            if kw.get("group_id"):
                beneficiary = request.env["res.partner"].sudo().browse(int(kw.get("group_id")))
                beneficiary.write(additional_data)
                beneficiary_id = beneficiary.id
            else:
                if head_name:
                    user = request.env.user

                    data = {
                        "is_registrant": True,
                        "is_group": True,
                        "user_id": user.id,
                    }

                    data.update(additional_data)
                    beneficiary_obj = request.env["res.partner"].sudo().create(data)
                    beneficiary_id = beneficiary_obj.id

                    # Create a group head as member
                    head_name_parts = head_name.split(" ")
                    h_given_name = head_name_parts[0]
                    h_family_name = head_name_parts[-1]

                    if len(head_name_parts) > 2:
                        h_addl_name = " ".join(head_name_parts[1:-1])
                    else:
                        h_addl_name = ""

                    formatted_name = f"{h_family_name} , {h_given_name} {h_addl_name}"

                    head_individual = (
                        request.env["res.partner"]
                        .sudo()
                        .create(
                            {
                                "name": formatted_name,
                                "given_name": h_given_name,
                                "addl_name": h_addl_name,
                                "family_name": h_family_name,
                                "email": kw.get("email"),
                                "address": kw.get("address"),
                                "birthdate": kw.get("birthdate"),
                                "gender": kw.get("gender"),
                                "is_registrant": True,
                                "is_group": False,
                                "user_id": user.id,
                            }
                        )
                    )

                    # Create membership relationship between head and group
                    group_membership_vals = [
                        (0, 0, {"individual": head_individual.id, "group": beneficiary_id})
                    ]

                    # Update the group with this membership
                    beneficiary_obj.write({"group_membership_ids": group_membership_vals})

            beneficiary = request.env["res.partner"].sudo().browse(beneficiary_id)

            if not beneficiary:
                return request.render(
                    "g2p_registration_portal_base.error_template",
                    {"error_message": "Beneficiary not found."},
                )

            return request.redirect("/portal/registration/group")

        except Exception as e:
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": "An error occurred. Please try again later."},
            )

    @http.route(
        ["/portal/registration/individual/create/"],
        type="http",
        auth="user",
        csrf=False,
    )
    def individual_registrar_create(self, **kw):
        self.check_roles("Agent")
        gender = request.env["gender.type"].sudo().search([])
        
        all_regions = request.env["g2p.region"].sudo().search([])
        unique_regions_map = {}
        for r in all_regions:
            if r.name not in unique_regions_map:
                unique_regions_map[r.name] = r
        regions = list(unique_regions_map.values())

        districts = request.env["g2p.district"].sudo().search([])
        return request.render(
            "g2p_registration_portal_base.individual_registrant_form_template",
            {"gender": gender, "regions": regions, "districts": districts},
        )

    @http.route(
        ["/portal/registration/individual/update/<int:_id>"],
        type="http",
        auth="user",
        csrf=False,
    )
    def indvidual_update(self, _id, **kw):
        self.check_roles("Agent")
        try:
            gender = request.env["gender.type"].sudo().search([])
            
            all_regions = request.env["g2p.region"].sudo().search([])
            unique_regions_map = {}
            for r in all_regions:
                if r.name not in unique_regions_map:
                    unique_regions_map[r.name] = r
            regions = list(unique_regions_map.values())

            districts = request.env["g2p.district"].sudo().search([])
            beneficiary = request.env["res.partner"].sudo().browse(_id)
            if not beneficiary:
                return request.render(
                    "g2p_registration_portal_base.error_template",
                    {"error_message": "Beneficiary not found."},
                )

            return request.render(
                "g2p_registration_portal_base.individual_update_form_template",
                {
                    "beneficiary": beneficiary,
                    "gender": gender,
                    "regions": regions,
                    "districts": districts,
                },
            )
        except Exception:
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": "Invalid URL."},
            )

    @http.route(
        ["/portal/registration/individual/view/<int:_id>"],
        type="http",
        auth="user",
        csrf=False,
    )
    def individual_view_details(self, _id, **kw):
        """
        View Individual Details (Read-Only)
        """
        self.check_roles("Agent")

        try:
            gender = request.env["gender.type"].sudo().search([])
            
            # Fetch Regions
            all_regions = request.env["g2p.region"].sudo().search([])
            unique_regions_map = {}
            for r in all_regions:
                if r.name not in unique_regions_map:
                    unique_regions_map[r.name] = r
            regions = list(unique_regions_map.values())

            # Fetch Districts
            districts = request.env["g2p.district"].sudo().search([])

            # Fetch Beneficiary
            beneficiary = request.env["res.partner"].sudo().browse(_id)

            if not beneficiary:
                return request.render(
                    "g2p_registration_portal_base.error_template",
                    {"error_message": "Beneficiary not found."},
                )

            return request.render(
                "g2p_social_registry_model.individual_view_details_readonly",
                {
                    "beneficiary": beneficiary,
                    "gender": gender,
                    "regions": regions,
                    "districts": districts,
                },
            )

        except Exception as e:
            _logger.exception("Error loading individual details view: %s", str(e))
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": "An error occurred while loading the view: " + str(e)},
            )

        return reg_ids

    def _get_reg_ids_command(self, kw):
        reg_ids = []
        if kw.get("other_id_available") == "yes":
            other_id_type_code = kw.get("other_id_type")
            other_id_number = kw.get("other_id_number")

            if other_id_type_code and other_id_number:
                # Simple mapping from form values to likely DB names
                type_map = {
                    "national_id": "National ID",
                    "passport": "Passport",
                    "driving_licence": "Driving Licence",
                    "voter_id": "Voter ID",
                    "other": "Other",
                }
                # Try mapped name, else fallback to code
                search_name = type_map.get(other_id_type_code, other_id_type_code)

                # Search for ID Type (case insensitive)
                id_type = request.env["g2p.id.type"].sudo().search([("name", "=ilike", search_name)], limit=1)

                if id_type:
                    reg_ids.append((0, 0, {
                        "id_type": id_type.id,
                        "value": other_id_number,
                        "status": "valid",
                        "description": kw.get("other_id_name")
                    }))

        # Zanzibar ID
        if kw.get("benf_zan_id"):
            id_type = request.env["g2p.id.type"].sudo().search([("name", "=", "Zanzibar ID")], limit=1)
            if id_type:
                reg_ids.append((0, 0, {
                    "id_type": id_type.id,
                    "value": kw.get("benf_zan_id"),
                    "status": "valid",
                }))

        # Nominee Zanzibar ID
        if kw.get("nominee_zanid"):
            id_type = request.env["g2p.id.type"].sudo().search([("name", "=", "Nominee Zanzibar ID")], limit=1)
            if id_type:
                reg_ids.append((0, 0, {
                    "id_type": id_type.id,
                    "value": kw.get("nominee_zanid"),
                    "status": "valid",
                }))
        
        return reg_ids

    @http.route(
        ["/portal/registration/individual/create/submit"],
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def individual_create_submit(self, **kw):
        try:
            user = request.env.user
            name = ""
            if kw.get("family_name"):
                name += kw.get("family_name") + ", "
            if kw.get("given_name"):
                name += kw.get("given_name") + " "
            if kw.get("addl_name"):
                name += kw.get("addl_name") + " "
            if kw.get("birthdate") == "":
                birthdate = False
            else:
                birthdate = kw.get("birthdate")

            data = {
                "given_name": kw.get("given_name"),
                "addl_name": kw.get("addl_name"),
                "family_name": kw.get("family_name"),
                "name": name.strip(),
                "birthdate": birthdate,
                "gender": kw.get("gender"),
                "email": kw.get("email"),
                "user_id": user.id,
                "is_registrant": True,
                "is_group": False,
                # Additional fields
                "address": ", ".join(filter(None, [kw.get("street"), kw.get("street2")])),
                "occupation": kw.get("occupation"),
                "income": float(kw.get("income", 0.0)) if kw.get("income") else 0.0,
                "education_level": kw.get("education_level"),
                "employment_status": kw.get("employment_status"),
                "marital_status": kw.get("marital_status"),
                # Nominee Info
                "nominee_first_name": kw.get("nominee_first_name"),
                "nominee_last_name": kw.get("nominee_last_name"),
                "nominee_mobile": kw.get("nominee_mobile"),
                "nominee_gender": kw.get("nominee_gender"),
                # "nominee_zanid" removed (stored in reg_ids)
                "nominee_rel_benf": kw.get("nominee_rel_benf"),
                "nominee_house_street": kw.get("nominee_house_street"),
                "nominee_shehia": kw.get("nominee_shehia"),
                "nominee_region": kw.get("nominee_region"),
                "nominee_district": kw.get("nominee_district"),
                # Pension Info
                "other_pension": kw.get("other_pension"),
                "scheme_name": kw.get("scheme_name"),
                # Payment Info
                "payment_mode": kw.get("payment_mode"),
                "bank_name": kw.get("bank_name"),
                "account_num": kw.get("account_num"),
                "account_name": kw.get("account_name"),
                "mobile_wallet": kw.get("mobile_wallet"),
                # New Fields
                "street": kw.get("street"),
                "street2": kw.get("street2"),
                "region": int(kw.get("region")) if kw.get("region") else False,
                "district": int(kw.get("district")) if kw.get("district") else False,
                "benf_post_code": kw.get("benf_post_code"),
                "benf_post_code": kw.get("benf_post_code"),
                # "benf_zan_id" removed (stored in reg_ids)
                "disability": kw.get("disability"),
                "is_receiving_allowance": kw.get("is_receiving_allowance"),
                "has_health_insurance": kw.get("has_health_insurance"),
                # Other ID (Flat fields kept for view compatibility)
                "other_id_available": kw.get("other_id_available"),
                "other_id_type": kw.get("other_id_type"),
                "other_id_name": kw.get("other_id_name"),
                "other_id_number": kw.get("other_id_number"),
            }

            # Add reg_ids logic
            reg_ids = self._get_reg_ids_command(kw)
            if reg_ids:
                data["reg_ids"] = reg_ids

            if kw.get("nominee_image"):
                data["nominee_image"] = base64.b64encode(kw.get("nominee_image").read())
            if kw.get("zan_image"):
                data["zan_image"] = base64.b64encode(kw.get("zan_image").read())
            if kw.get("beneficiary_image"):
                data["beneficiary_image"] = base64.b64encode(kw.get("beneficiary_image").read())

            partner = request.env["res.partner"].sudo().create(data)
            if kw.get("mobile"):
                request.env["g2p.phone.number"].sudo().create(
                    {
                        "partner_id": partner.id,
                        "phone_no": kw.get("mobile"),
                    }
                )
                # Sync phone field for list view
                partner.sudo().write({"phone": kw.get("mobile")})

            return request.redirect("/portal/registration/individual")

        except Exception as e:
            _logger.exception("Error while submitting individual registration: %s", str(e))
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": f"Error while submitting individual registration: {str(e)}"},
            )

    @http.route(
        "/portal/registration/individual/update/submit",
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def update_individual_submit(self, **kw):
        try:
            member = request.env["res.partner"].sudo().browse(int(kw.get("group_id")))
            if member:
                name = ""
                if kw.get("family_name"):
                    name += kw.get("family_name") + ", "
                if kw.get("given_name"):
                    name += kw.get("given_name") + " "
                if kw.get("addl_name"):
                    name += kw.get("addl_name") + " "
                if kw.get("birthdate") == "":
                    birthdate = False
                else:
                    birthdate = kw.get("birthdate")

                vals = {
                    "given_name": kw.get("given_name"),
                    "addl_name": kw.get("addl_name"),
                    "family_name": kw.get("family_name"),
                    "name": name,
                    "birthdate": birthdate,
                    "gender": kw.get("gender"),
                    "email": kw.get("email"),
                    "address": ", ".join(filter(None, [kw.get("street"), kw.get("street2")])),
                    "occupation": kw.get("occupation"),
                    "income": float(kw.get("income", 0.0)),
                    # Household Details
                    "education_level": kw.get("education_level"),
                    "employment_status": kw.get("employment_status"),
                    "marital_status": kw.get("marital_status"),
                    # Nominee Info
                    "nominee_first_name": kw.get("nominee_first_name"),
                    "nominee_last_name": kw.get("nominee_last_name"),
                    "nominee_mobile": kw.get("nominee_mobile"),
                    "nominee_gender": kw.get("nominee_gender"),
                    # "nominee_zanid" removed (stored in reg_ids)
                    "nominee_rel_benf": kw.get("nominee_rel_benf"),
                    "nominee_house_street": kw.get("nominee_house_street"),
                    "nominee_shehia": kw.get("nominee_shehia"),
                    "nominee_region": kw.get("nominee_region"),
                    "nominee_district": kw.get("nominee_district"),
                    # Pension Info
                    "other_pension": kw.get("other_pension"),
                    "scheme_name": kw.get("scheme_name"),
                    # Payment Info
                    "payment_mode": kw.get("payment_mode"),
                    "bank_name": kw.get("bank_name"),
                    "account_num": kw.get("account_num"),
                    "account_name": kw.get("account_name"),
                    "mobile_wallet": kw.get("mobile_wallet"),
                    # New Fields
                    "street": kw.get("street"),
                    "street2": kw.get("street2"),
                    "region": int(kw.get("region")) if kw.get("region") else False,
                    "district": int(kw.get("district")) if kw.get("district") else False,
                    "benf_post_code": kw.get("benf_post_code"),
                    "benf_post_code": kw.get("benf_post_code"),
                    # "benf_zan_id" removed (stored in reg_ids)
                    "disability": kw.get("disability"),
                    "is_receiving_allowance": kw.get("is_receiving_allowance"),
                    "has_health_insurance": kw.get("has_health_insurance"),
                    # Other ID (Flat fields kept for view compatibility)
                    "other_id_available": kw.get("other_id_available"),
                    "other_id_type": kw.get("other_id_type"),
                    "other_id_name": kw.get("other_id_name"),
                    "other_id_number": kw.get("other_id_number"),
                }

                # ID Handling Logic
                reg_ids_commands = []
                if kw.get("other_id_available") == "yes":
                    other_id_type_code = kw.get("other_id_type")
                    other_id_number = kw.get("other_id_number")

                    if other_id_type_code and other_id_number:
                        type_map = {
                            "national_id": "National ID",
                            "passport": "Passport",
                            "driving_licence": "Driving Licence",
                            "voter_id": "Voter ID",
                            "other": "Other",
                        }
                        search_name = type_map.get(other_id_type_code, other_id_type_code)
                        id_type = request.env["g2p.id.type"].sudo().search([("name", "=ilike", search_name)], limit=1)

                        if id_type:
                            # Check if member already has this ID type
                            existing_id = member.reg_ids.filtered(lambda r: r.id_type.id == id_type.id)
                            
                            vals_id = {
                                "value": other_id_number,
                                "status": "valid",
                                "description": kw.get("other_id_name")
                            }

                            if existing_id:
                                # Update existing ID if value changed or just update metadata
                                # Using (1, id, values) for update
                                reg_ids_commands.append((1, existing_id[0].id, vals_id))
                            else:
                                # Create new ID
                                # Using (0, 0, values) for create
                                reg_ids_commands.append((0, 0, {
                                    "id_type": id_type.id,
                                    **vals_id
                                }))

                # Zanzibar ID
                if kw.get("benf_zan_id"):
                    id_type = request.env["g2p.id.type"].sudo().search([("name", "=", "Zanzibar ID")], limit=1)
                    if id_type:
                        existing_id = member.reg_ids.filtered(lambda r: r.id_type.id == id_type.id)
                        vals_id = {"value": kw.get("benf_zan_id"), "status": "valid"}
                        if existing_id:
                            reg_ids_commands.append((1, existing_id[0].id, vals_id))
                        else:
                            reg_ids_commands.append((0, 0, {"id_type": id_type.id, **vals_id}))

                # Nominee Zanzibar ID
                if kw.get("nominee_zanid"):
                    id_type = request.env["g2p.id.type"].sudo().search([("name", "=", "Nominee Zanzibar ID")], limit=1)
                    if id_type:
                        existing_id = member.reg_ids.filtered(lambda r: r.id_type.id == id_type.id)
                        vals_id = {"value": kw.get("nominee_zanid"), "status": "valid"}
                        if existing_id:
                            reg_ids_commands.append((1, existing_id[0].id, vals_id))
                        else:
                            reg_ids_commands.append((0, 0, {"id_type": id_type.id, **vals_id}))

                if reg_ids_commands:
                    vals["reg_ids"] = reg_ids_commands

                member.sudo().write(vals)

                if kw.get("mobile"):
                    # Check if the member already has a phone number
                    existing_phone = member.phone_number_ids.filtered(lambda p: not p.disabled)
                    if existing_phone:
                        # If the number is different, disable the old one and create a new one
                        if existing_phone[0].phone_no != kw.get("mobile"):
                            existing_phone[0].write(
                                {"disabled": fields.Datetime.now(), "disabled_by": request.env.user.id}
                            )
                            request.env["g2p.phone.number"].sudo().create(
                                {
                                    "partner_id": member.id,
                                    "phone_no": kw.get("mobile"),
                                }
                            )
                    else:
                        # If no phone number exists, create a new one
                        request.env["g2p.phone.number"].sudo().create(
                            {
                                "partner_id": member.id,
                                "phone_no": kw.get("mobile"),
                            }
                        )
                    
                    # Sync phone field for list view
                    member.sudo().write({"phone": kw.get("mobile")})

                if kw.get("nominee_image"):
                    member.sudo().write({"nominee_image": base64.b64encode(kw.get("nominee_image").read())})
                if kw.get("zan_image"):
                    member.sudo().write({"zan_image": base64.b64encode(kw.get("zan_image").read())})
                if kw.get("beneficiary_image"):
                    member.sudo().write({"beneficiary_image": base64.b64encode(kw.get("beneficiary_image").read())})
            return request.redirect("/portal/registration/individual")

        except Exception as e:
            _logger.error("Error occurred: %s" % e)
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": f"An error occurred: {str(e)}"},
            )
