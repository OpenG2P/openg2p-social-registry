import json
import logging
from datetime import date, datetime

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class BaseInherit(models.AbstractModel):
    _inherit = "base"

    def web_save(self, vals, specification: dict[str, dict], next_id=None) -> list[dict]:
        if self._name == "res.partner" and self.env.context.get("draft"):
            self.action_save_to_draft(vals)
            return self

        if self:
            self.write(vals)
        else:
            self = self.create(vals)
        if next_id:
            self = self.browse(next_id)
        return self.with_context(bin_size=True).web_read(specification)


class G2PDraftRecord(models.Model):
    _name = "draft.record"
    _description = "Draft Imported Records"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char()
    given_name = fields.Char()
    family_name = fields.Char()
    addl_name = fields.Char()
    phone = fields.Char()
    gender = fields.Char()
    region = fields.Char()

    partner_data = fields.Json(string="Partner Data (JSON)")
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("published", "Published"),
            ("rejected", "Rejected"),
        ],
        default="draft",
    )
    rejection_reason = fields.Text("remark")

    @api.model
    def create(self, vals):
        # Custom logic before creation
        phone_number_ids = [(0, 0, {"phone_no": vals["phone"]})]
        partner_data = {
            "given_name": vals["given_name"],
            "family_name": vals["family_name"],
            "addl_name": vals["addl_name"],
            "phone_number_ids": phone_number_ids,
            "gender": vals["gender"],
            "region": vals["region"],
        }
        vals["partner_data"] = json.dumps(partner_data)

        self.sudo().write({"message_partner_ids": [(6, 0, self.message_partner_ids.ids)]})
        record = super().create(vals)
        return record

    def action_change_state(self):
        return {
            "name": "Confirm Rejection",
            "type": "ir.actions.act_window",
            "res_model": "change.state.wizard",
            "view_mode": "form",
            "view_id": self.env.ref("g2p_draft_publish.change_state_wizard_view").id,
            "target": "new",
        }

    def action_publish(self):
        self.ensure_one()
        partner_data = json.loads(self.partner_data)
        res_partner_model = self.env["res.partner"]

        fields_metadata = res_partner_model.fields_get()

        valid_data = {}

        given_name = partner_data.get("given_name", "")
        family_name = partner_data.get("family_name", "")
        gf_name_en = partner_data.get("addl_name", "")

        for field_name, value in partner_data.items():
            if field_name in fields_metadata:
                field_info = fields_metadata[field_name]
                field_type = field_info.get("type")

                if field_type == "char" and isinstance(value, str):
                    valid_data[field_name] = value
                elif field_type == "integer" and isinstance(value, int):
                    valid_data[field_name] = value
                elif field_type == "float" and isinstance(value, int | float):
                    valid_data[field_name] = float(value)
                elif field_type == "boolean" and isinstance(value, bool):
                    valid_data[field_name] = value
                elif field_type == "many2one" and isinstance(value, int):
                    # Check if the referenced record exists
                    if self.env[field_info["relation"]].browse(value).exists():
                        valid_data[field_name] = value
                elif field_type == "selection":
                    selection_options = [option[0] for option in field_info.get("selection", [])]
                    if value in selection_options:
                        valid_data[field_name] = value

        # Create the res.partner record with valid data
        if valid_data:
            valid_data["db_import"] = "yes"
            valid_data["name"] = f"{given_name} {family_name} {gf_name_en}".upper()

            res_partner_model.create(valid_data)
            self.write({"state": "published"})

            validator_group = self.env.ref("g2p_draft_publish.group_int_validator")
            admin_group = self.env.ref("g2p_draft_publish.group_int_admin")
            approver_group = self.env.ref("g2p_draft_publish.group_int_approver")
            validator_users = validator_group.users
            exclusive_validator_users = validator_users.filtered(
                lambda user: user not in admin_group.users and user not in approver_group.users
            )
            matching_users = exclusive_validator_users.filtered(
                lambda user: user.partner_id.id in self.message_partner_ids.ids
            )

            if matching_users:
                for user in matching_users:
                    self.message_post(
                        _(
                            body="Record has been published",
                            subject="Record Published",
                            message_type="notification",
                            partner_ids=[user.partner_id.id],
                        )
                    )

        else:
            raise ValueError("No valid data found to create a partner record.")

    def action_submit(self):
        activities = self.env["mail.activity"].search(
            [("res_model", "=", self._name), ("res_id", "in", self.ids)]
        )
        if activities:
            activities.action_done()

        self.write({"state": "submitted"})

    def action_open_wizard(self):
        self.ensure_one()
        active_id = self.id

        if not self.partner_data:
            raise UserError(_("No partner data available to edit."))

        try:
            json_data = json.loads(self.partner_data)
        except json.JSONDecodeError as err:
            raise UserError(_("Invalid JSON data in partner_data.")) from err

        context_data, additional_g2p_info = self._process_json_data(json_data)

        context_data["active_id"] = active_id

        return {
            "type": "ir.actions.act_window",
            "name": "Record Data",
            "view_mode": "form",
            "res_model": "res.partner",
            "view_id": self.env.ref("g2p_draft_publish.g2p_validation_form_view").id,
            "target": "new",
            "context": {
                **context_data,
                "default_additional_g2p_info": json.dumps(additional_g2p_info),
                "draft": "yes",
                "default_phone_number_ids": json_data.get("phone_number_ids", []),
                "default_individual_membership_ids": json_data.get("individual_membership_ids", []),
                "default_reg_ids": json_data.get("reg_ids", []),
            },
        }

    def _process_json_data(self, json_data):
        partner_model_fields = self.env["res.partner"]._fields
        additional_g2p_info = {}
        context_data = {}

        for field_name, field_value in json_data.items():
            if field_name not in partner_model_fields:
                additional_g2p_info[field_name] = field_value
                continue

            field = partner_model_fields[field_name]

            if field.type == "datetime" and isinstance(field_value, str):
                field_value = datetime.fromisoformat(field_value)
                context_data[f"default_{field_name}"] = field_value

            elif field.type == "date" and isinstance(field_value, str):
                field_value = date.fromisoformat(field_value)
                context_data[f"default_{field_name}"] = field_value

            elif (field.type == "char" or field.type == "text") and isinstance(field_value, str):
                context_data[f"default_{field_name}"] = field_value

            elif field.type == "many2one":
                if isinstance(field_value, int):
                    field_value = int(field_value)
                    context_data[f"default_{field_name}"] = json_data[field_name]
                else:
                    additional_g2p_info[field_name] = field_value

            elif field.type == "many2many":
                if isinstance(field_value, list):
                    if all(isinstance(val, int) for val in field_value):
                        context_data[f"default_{field_name}"] = [(6, 0, field_value)]
                    elif all(hasattr(val, "id") for val in field_value):
                        context_data[f"default_{field_name}"] = [(6, 0, [val.id for val in field_value])]
                    else:
                        additional_g2p_info[field_name] = field_value
                elif hasattr(field_value, "id"):
                    context_data[f"default_{field_name}"] = [(6, 0, [field_value.id])]
                else:
                    additional_g2p_info[field_name] = field_value

            elif field.type == "selection":
                selection_values = field.get_values(env=self.env)
                if field_value in selection_values:
                    context_data[f"default_{field_name}"] = field_value
                if field_value not in selection_values:
                    additional_g2p_info[field_name] = field_value

            else:
                context_data[f"default_{field_name}"] = field_value

        return context_data, additional_g2p_info

    def action_reject(self):
        return {
            "name": "Confirm Rejection",
            "type": "ir.actions.act_window",
            "res_model": "reject.wizard",
            "view_mode": "form",
            "target": "new",
        }


class G2PRespartnerIntegration(models.Model):
    _inherit = "res.partner"

    db_import = fields.Selection(
        string="Imported", index=True, selection=[("yes", "Yes"), ("no", "No")], default="no"
    )

    def action_update(self):
        return

    def action_save_to_draft(self, vals):
        context = self.env.context
        model_name = context.get("active_model")
        record_id = context.get("active_id")
        active_record = self.env[model_name].browse(record_id)
        partner_data = json.loads(active_record.partner_data) or {}

        m2m_fields = {
            "tags_ids": "tags_ids",
        }

        processed_m2m_fields = {}
        for field in m2m_fields:
            processed_m2m_fields[field] = [item[1] for item in vals.get(field, [])]
        dynamic_fields = {
            "is_company": False,
            "is_group": False,
            "is_registrant": True,
            "db_import": "yes",
            **processed_m2m_fields,
        }

        static_fields = self.get_fields_in_view()

        draft_record = {}

        draft_record.update(dynamic_fields)

        for field in static_fields:
            if field in self.env[model_name]._fields:
                draft_record[field] = vals.get(field) or partner_data.get(field)
            else:
                if vals.get(field):
                    draft_record[field] = vals[field]

        if vals.get("given_name") or vals.get("family_name") or vals.get("addl_name"):
            
            name_parts = [
                val.upper() for val in [
                    vals.get("given_name"),
                    vals.get("family_name"),
                    vals.get("addl_name")
                    ] if val
                ]
            
            
            draft_record["name"] = " ".join(filter(None, name_parts)).strip()

        active_record.write({"partner_data": json.dumps(draft_record)})

    def action_publish(self):
        context = self.env.context
        model_name = context.get("active_model")
        record_id = context.get("active_id")
        record = self.env[model_name].browse(record_id)
        if record.state == "published":
            raise ValidationError(_("Record already has been published"))
        else:
            record.action_publish()

    def action_submit(self):
        context = self.env.context
        model_name = context.get("active_model")
        record_id = context.get("active_id")
        record = self.env[model_name].browse(record_id)
        if record.state == "submitted":
            raise ValidationError(_("Record already has been Submitted"))
        else:
            record.action_submit()

    def get_fields_in_view(self):
        views = self.env["ir.ui.view"].search(
            [
                ("model", "=", "res.partner"),
                ("type", "=", "form"),  # Assuming you want to get fields from form view
            ]
        )

        # Initialize a set to store field names from all views (base and inherited)
        fields_in_view = set()

        # Loop through each view (including inherited ones)
        for view in views:
            # Get the architecture of the view
            arch = view.arch

            # Use lxml to parse the XML
            root = etree.fromstring(arch)

            # Loop through all the <field> tags and collect the field names
            for field in root.xpath("//field"):
                field_name = field.get("name")
                if field_name:
                    fields_in_view.add(field_name)

        # Now compare fields_in_view with actual fields in the model
        all_fields_in_model = set(self._fields.keys())
        usable_fields = all_fields_in_model.intersection(fields_in_view)

        return usable_fields