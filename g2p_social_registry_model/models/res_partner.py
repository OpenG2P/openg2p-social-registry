# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging

from odoo import fields, models
from odoo.addons.g2p_document_field.image_field import DocumentImageField

_logger = logging.getLogger(__name__)


class G2PResPartnerInherited(models.Model):
    _inherit = "res.partner"

    #######################################################
    #####          Social Status Information          #####
    #######################################################

    num_preg_lact_women = fields.Integer("Pregnant & Lactating Women")
    num_malnourished_children = fields.Integer("Malnourished Children Under 5")
    num_disabled = fields.Integer("No. of member with Disability")
    type_of_disability = fields.Selection(
        [
            ("visual_impairment", "Visual Impairment"),
            ("hearing_impairment", "Hearing Impairment"),
            ("physical_disability", "Physical Disability"),
            ("cognitive_disability", "Cognitive Disability"),
        ]
    )
    caste_ethnic_group = fields.Selection(
        [
            ("bantu", "Bantu"),
            ("nilotic", "Nilotic"),
            ("afro_asian", "Afro-Asiatic"),
            ("khoisan", "Khoisan"),
            ("pygmy", "Pygmy"),
            ("other", "Other"),
        ],
        "Caste/Ethnic Group",
    )
    belong_to_protected_groups = fields.Selection(
        [("yes", "Yes"), ("no", "No")], "Belong to any protected groups?"
    )
    other_vulnerable_status = fields.Selection(
        [("yes", "Yes"), ("no", "No")], "Under any other vulnerable status?"
    )

    #######################################################
    #####              Household Details              #####
    #######################################################

    education_level = fields.Selection(
        [
            ("primary", "Primary"),
            ("secondary", "Secondary"),
            ("higher_secondary", "Higher Secondary"),
            ("bachelors", "Bachelors"),
            ("masters", "Masters"),
        ]
    )
    employment_status = fields.Selection(
        [
            ("employed_full", "Employed - Full Time"),
            ("employed_part", "Employed - Part Time"),
            ("self_employed", "Self-employed"),
            ("unemployed", "Unemployed"),
        ]
    )
    marital_status = fields.Selection(
        [("single", "Single"), ("married", "Married"), ("divorced", "divorced")]
    )

    #######################################################
    #####         Economic Status Information         #####
    #######################################################

    income_sources = fields.Selection(
        [
            ("agriculture", "Agriculture"),
            ("business", "Business"),
            ("mining", "Mining"),
            ("manufacturing", "Manufacturing"),
            ("construction", "Construction"),
        ],
        "Sources of Income",
    )
    annual_income = fields.Selection(
        [("below_5000", "Below 5000"), ("5001_10000", "5001-10,000"), ("above_10000", "Above 10,000")],
    )
    owns_two_wheeler = fields.Selection([("yes", "Yes"), ("no", "No")], "Owns a Two-Wheeler")
    owns_three_wheeler = fields.Selection([("yes", "Yes"), ("no", "No")], "Owns a Three-Wheeler")
    owns_four_wheeler = fields.Selection([("yes", "Yes"), ("no", "No")], "Owns a Four-Wheeler")
    owns_cart = fields.Selection([("yes", "Yes"), ("no", "No")], "Owns a Cart")
    land_ownership = fields.Selection([("yes", "Yes"), ("no", "No")])
    type_of_land_owned = fields.Selection(
        [
            ("agricultural", "Agricultural Land"),
            ("residential", "Residential Land"),
            ("pastoral", "Pastoral Land"),
            ("forest", "Forest Land"),
            ("commercial", "Commercial Land"),
            ("communal", "Communal Land"),
            ("other", "Other"),
        ]
    )
    land_size = fields.Float()
    owns_house = fields.Selection([("yes", "Yes"), ("no", "No")])
    owns_livestock = fields.Selection([("yes", "Yes"), ("no", "No")])

    #######################################################
    #####        Housing Condition Information        #####
    #######################################################

    housing_type = fields.Selection(
        [("permanent", "Permanent"), ("temporary", "Temporary")], "Type of Housing"
    )
    house_condition = fields.Selection([("mud", "Mud"), ("cement", "Cement")])
    sanitation_condition = fields.Selection([("yes", "Yes"), ("no", "No")])
    water_access = fields.Selection([("yes", "Yes"), ("no", "No")])
    electricity_access = fields.Selection([("yes", "Yes"), ("no", "No")])

    #######################################################
    #####               Attachment Fields             #####
    #######################################################

    nominee_image = DocumentImageField(
        string="Relative / Nominee Photo",
        documents_field="supporting_documents_ids",
        get_tags_func="_get_nominee_image_tags",
        get_storage_backend_func="get_registry_documents_store",
        max_width=1024,
        max_height=1024,
    )
    zan_image = DocumentImageField(
        string="Zan ID Photo",
        documents_field="supporting_documents_ids",
        get_tags_func="_get_zan_image_tags",
        get_storage_backend_func="get_registry_documents_store",
        max_width=1024,
        max_height=1024,
    )
    beneficiary_image = DocumentImageField(
        string="Beneficiary Photo",
        documents_field="supporting_documents_ids",
        get_tags_func="_get_beneficiary_image_tags",
        get_storage_backend_func="get_registry_documents_store",
        max_width=1024,
        max_height=1024,
    )

    def _get_nominee_image_tags(self):
        return self.env["g2p.document.tag"].sudo().get_or_create_tag_from_name("Nominee Photo")

    def _get_zan_image_tags(self):
        return self.env["g2p.document.tag"].sudo().get_or_create_tag_from_name("Zan ID Photo")

    def _get_beneficiary_image_tags(self):
        return self.env["g2p.document.tag"].sudo().get_or_create_tag_from_name("Beneficiary Photo")
