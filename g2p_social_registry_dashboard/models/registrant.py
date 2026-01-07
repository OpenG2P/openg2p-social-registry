# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class ResPartnerDashboard(models.Model):
    _inherit = "res.partner"

    @api.model
    def get_dashboard_data(self):
        """Fetch data from materialized view and prepare it for charts."""
        company_id = self.env.company.id

        query = """
            SELECT total_registrants, gender_spec, age_distribution
            FROM g2p_sr_dashboard_data
            WHERE company_id = %s
        """
        self.env.cr.execute(query, (company_id,))
        result = self.env.cr.fetchone()

        if not result:
            return {
                "total_individuals": 0,
                "gender_distribution": {},
                "age_distribution": {
                    "Below 18": 0,
                    "18 to 30": 0,
                    "31 to 40": 0,
                    "41 to 50": 0,
                    "51 to 60": 0,
                    "61 to 70": 0,
                    "Above 70": 0,
                },
            }

        total_registrants, gender_spec, age_distribution = result
        total_registrants = total_registrants or {}
        gender_spec = gender_spec or {}
        age_distribution = age_distribution or {}

        return {
            "total_individuals": total_registrants.get("total_individuals", 0),
            "gender_distribution": gender_spec,
            "age_distribution": {
                "Below 18": age_distribution.get("below_18", 0),
                "18 to 30": age_distribution.get("18_to_30", 0),
                "31 to 40": age_distribution.get("31_to_40", 0),
                "41 to 50": age_distribution.get("41_to_50", 0),
                "51 to 60": age_distribution.get("51_to_60", 0),
                "61 to 70": age_distribution.get("61_to_70", 0),
                "Above 70": age_distribution.get("above_70", 0),
            },
        }
