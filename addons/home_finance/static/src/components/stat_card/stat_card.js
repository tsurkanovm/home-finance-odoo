/** @odoo-module **/
import { Component } from "@odoo/owl";

export class StatCard extends Component {
    static template = "home_finance.StatCard";
    static props = {
        title: String,
        value: [String, Number],
        subtitle: { type: String, optional: true },
        icon: { type: String, optional: true },
        variant: { type: String, optional: true },
    };
}
