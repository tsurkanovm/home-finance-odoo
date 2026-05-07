/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { StatCard } from "../components/stat_card/stat_card";
import { ExpenseChart } from "../components/expense_chart/expense_chart";

function lastNPeriods(currentPeriod, n) {
    const parts = currentPeriod.split("-").map(Number);
    const year = parts[0];
    const month = parts[1];
    const periods = [];
    for (let i = n - 1; i >= 0; i--) {
        let m = month - i;
        let y = year;
        while (m <= 0) {
            m += 12;
            y--;
        }
        const lastDay = new Date(y, m, 0).getDate();
        periods.push(
            `${y}-${String(m).padStart(2, "0")}-${String(lastDay).padStart(2, "0")}`
        );
    }
    return periods;
}

class HfDashboard extends Component {
    static template = "home_finance.Dashboard";
    static components = { StatCard, ExpenseChart };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            loading: true,
            currentPeriod: null,
            balances: [],
            totalExpense: 0,
            totalIncome: 0,
            topCategories: [],
            trendData: [],
            filterMonths: 6,
        });
        onWillStart(() => this.loadData());
    }

    async loadData() {
        this.state.loading = true;

        const [param] = await this.orm.searchRead(
            "ir.config_parameter",
            [["key", "=", "home_finance.current_period"]],
            ["value"],
            { limit: 1 }
        );
        const period = param ? param.value : null;
        this.state.currentPeriod = period;

        const balancesResult = await this.orm.webReadGroup(
            "home_finance.wallet.balance",
            [["amount", "<>", 0],["wallet_id.type", "<>", "invest"]],
            ["currency_id"],
            ["amount:sum"]
        );
        this.state.balances = balancesResult.groups;

        if (period) {
            const expenseResult = await this.orm.webReadGroup(
                "home_finance.transaction",
                [["period", "=", period], ["type", "=", "expense"], ["active", "=", true]],
                ["type"],
                ["base_amount:sum"]
            );
            this.state.totalExpense = expenseResult.groups[0]?.["base_amount:sum"] || 0;

            const incomeResult = await this.orm.webReadGroup(
                "home_finance.transaction",
                [["period", "=", period], ["type", "=", "income"], ["active", "=", true]],
                ["type"],
                ["base_amount:sum"]
            );
            this.state.totalIncome = incomeResult.groups[0]?.["base_amount:sum"] || 0;

            const topCategoriesResult = await this.orm.webReadGroup(
                "home_finance.transaction",
                [["period", "=", period], ["type", "=", "expense"], ["active", "=", true]],
                ["category_id"],
                ["base_amount:sum"],
                { order: "base_amount:sum desc", limit: 5 }
            );
            this.state.topCategories = topCategoriesResult.groups;

            const periods = lastNPeriods(period, this.state.filterMonths);
            const trendResult = await this.orm.webReadGroup(
                "home_finance.transaction",
                [["period", "in", periods], ["type", "=", "expense"], ["active", "=", true]],
                ["period:day"],
                ["base_amount:sum"]
            );
            this.state.trendData = periods.map((p) => {
                const found = trendResult.groups.find((d) => d["period:day"][0] === p);
                return { period: p, base_amount: found ? found["base_amount:sum"] || 0 : 0 };
            });
        }

        this.state.loading = false;
    }

    async setFilter(months) {
        this.state.filterMonths = months;
        await this.loadData();
    }

    get balanceSummary() {
        if (!this.state.balances.length) return "No data";
        return this.state.balances
            .map((b) => `${this._fmt(b["amount:sum"])} ${b.currency_id[1]}`)
            .join(" | ");
    }

    get formattedExpense() {
        return this._fmt(this.state.totalExpense);
    }

    get formattedIncome() {
        return this._fmt(this.state.totalIncome);
    }

    get topCategoryName() {
        if (!this.state.topCategories.length) return "None";
        const top = this.state.topCategories[0];
        const name = top.category_id ? top.category_id[1] : "Uncategorized";
        return `${name} ${this._fmt(top["base_amount:sum"])}`;
    }

    _fmt(value) {
        return new Intl.NumberFormat(undefined, {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(value || 0);
    }
}

registry.category("actions").add("home_finance.dashboard", HfDashboard);
