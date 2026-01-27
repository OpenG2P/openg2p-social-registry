/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { ChartComponent } from "../components/chart/chart";
import { KpiComponent } from "../components/kpi/kpi";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { session } from "@web/session";

class SRDashboard extends Component {
    setup() {
        super.setup();
        this._t = _t;
        this.orm = useService("orm");

        const lang = session.user_context.lang;
        this.isSwahili = lang === "sw" || lang === "sw_TZ";

        this.dashboard_title = this.isSwahili ? "Dashibodi ya Usajili ya Zanzibar" : _t("Zanzibar Registry Dashboard");
        this.labels = {
            individuals: this.isSwahili ? "Watu" : _t("Individuals"),
            age_distribution: this.isSwahili ? "Usambazaji wa Umri" : _t("Age Distribution"),
            gender_distribution: this.isSwahili ? "Usambazaji wa Jinsia" : _t("Gender Distribution"),
            region_distribution: this.isSwahili ? "Usambazaji wa Mkoa" : _t("Region Distribution"),
            male: this.isSwahili ? "Mwanamume" : _t("Male"),
            female: this.isSwahili ? "Mwanamke" : _t("Female"),
            below_18: this.isSwahili ? "Chini ya 18" : _t("Below 18"),
            above_70: this.isSwahili ? "Zaidi ya 70" : _t("Above 70"),
            to: this.isSwahili ? "hadi" : _t("to"),
        };

        this.dashboard_data = useState({
            total_individuals: 0,
            gender_distribution_keys: [],
            gender_distribution_values: [],
            age_distribution_keys: [],
            age_distribution_values: [],
            region_distribution_keys: [],
            region_distribution_values: [],
        });

        this.barChartOptions = {
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                    },
                },
            },
        };

        this.dataLoaded = useState({ flag: false });

        this.fetchData();
    }

    async fetchData() {
        try {
            const data = await this.orm.call("res.partner", "get_dashboard_data", []);

            data.gender_distribution_keys = Object.keys(data.gender_distribution).map(key => {
                const lowerKey = key.toLowerCase();
                if (lowerKey === "male") return this.labels.male;
                if (lowerKey === "female") return this.labels.female;
                return key;
            });
            data.gender_distribution_values = Object.values(data.gender_distribution);

            data.age_distribution_keys = Object.keys(data.age_distribution).map(key => {
                let trans = key;
                if (this.isSwahili) {
                    trans = trans.replace("Below", "Chini ya")
                        .replace("Above", "Zaidi ya")
                        .replace("to", "hadi");
                } else {
                    trans = _t(trans);
                }
                return trans;
            });
            data.age_distribution_values = Object.values(data.age_distribution);
            data.region_distribution_keys = Object.keys(data.region_distribution);
            data.region_distribution_values = Object.values(data.region_distribution);

            Object.assign(this.dashboard_data, data);

            this.dataLoaded.flag = true;
        } catch (error) {
            console.error("Error fetching dashboard data:", error);
        }
    }
}

SRDashboard.template = "g2p_social_registry_dashboard.dashboard_template";
SRDashboard.components = { ChartComponent, KpiComponent };

registry.category("actions").add("g2p_social_registry_dashboard.sr_dashboard_tag", SRDashboard);
