import odoo.addons.g2p_odk_importer.models.odk_client as base_odk_client

original_individual_data = base_odk_client.ODKClient.get_individual_data


def patched_individual_data(self, record):
    res = original_individual_data(self, record)

    if record.get("reg_ids"):
        res.update(
            {
                "reg_ids": [
                    (
                        0,
                        0,
                        {
                            "id_type": self.env["g2p.id.type"]
                            .search([("name", "=", reg_id.get("id_type"))], limit=1)
                            .id,
                            "value": reg_id.get("value"),
                            "expiry_date": reg_id.get("expiry_date"),
                            "status": "valid",
                        },
                    )
                    for reg_id in record.get("reg_ids")
                ],
                "education_level": record.get("education_level", None),
                "employment_status": record.get("employment_status", None),
                "marital_status": record.get("marital_status", None),
            }
        )
    return res


# def patched_member_relationship(self, source_id, record):
#     print(record)
#     relation = self.env["g2p.relationship"].search(
#         [("name", "=", record.get("household_member").get("relationship_with_household_head"))], limit=1
#     )
#     print('--- relation', relation)

#     if relation and source_id:
#         return {"source": source_id, "relation": relation.id, "start_date": datetime.now()}

#     return None


base_odk_client.ODKClient.get_individual_data = patched_individual_data
# base_odk_client.ODKClient.get_member_relationship = patched_member_relationship
