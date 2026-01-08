# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class ResPartnerDashboard(models.Model):
    _inherit = "res.partner"

    @api.model
    def get_dashboard_data(self):
        """Fetch data from materialized view and prepare it for charts."""
        company_id = self.env.company.id
        cr = self.env.cr

        # Check if the view needs updating (e.g., if columns were recently added)
        cr.execute("SELECT * FROM g2p_sr_dashboard_data LIMIT 0")
        colnames = [desc[0] for desc in cr.description]

        if "region_distribution" not in colnames:
            needs_refresh = True
        else:
            # Check if we have all regions (Cross Join) or just non-zero ones (Old Logic)
            cr.execute("SELECT COUNT(*) FROM g2p_region_distribution_view")
            view_row_count = cr.fetchone()[0]
            cr.execute("SELECT COUNT(*) FROM g2p_region")
            total_regions = cr.fetchone()[0]
            # If the count is different, it means the view is outdated (missing rows or has 'Unknown')
            needs_refresh = view_row_count != total_regions

        if needs_refresh:
            # Import and run the init function from the module level
            try:
                from odoo.addons.g2p_social_registry_dashboard import init_materialized_view, drop_materialized_view
                # Drop everything to ensure the NEW SQL logic for regions is applied
                drop_materialized_view(self.env)
                init_materialized_view(self.env)
                self.env.cr.commit() # Commit so the next query sees the new columns
            except Exception as e:
                _logger.error("Failed to refresh dashboard views: %s", str(e))
                pass

        query = """
            SELECT total_registrants, gender_spec, age_distribution, region_distribution
            FROM g2p_sr_dashboard_data
            WHERE company_id = %s
        """
        cr.execute(query, (company_id,))
        result = cr.fetchone()

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
                "region_distribution": {},
            }

        total_registrants, gender_spec, age_distribution, region_distribution = result
        total_registrants = total_registrants or {}
        gender_spec = gender_spec or {}
        age_distribution = age_distribution or {}
        region_distribution = region_distribution or {}

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
            "region_distribution": region_distribution,
        }
