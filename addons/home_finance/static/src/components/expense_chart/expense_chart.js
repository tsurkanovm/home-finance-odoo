/** @odoo-module **/
import { Component, useRef, onMounted, onWillUpdateProps, onWillUnmount } from "@odoo/owl";

// chart.js is loaded as a UMD global via the asset bundle
const { Chart } = window;

export class ExpenseChart extends Component {
    static template = "home_finance.ExpenseChart";
    static props = {
        data: Array,
    };

    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;

        onMounted(() => this._renderChart(this.props.data));
        onWillUpdateProps((next) => {
            this.chart?.destroy();
            this._renderChart(next.data);
        });
        onWillUnmount(() => this.chart?.destroy());
    }

    _renderChart(data) {
        const labels = data.map((d) => {
            const [y, m] = d.period.split("-");
            return new Date(y, m - 1).toLocaleDateString(undefined, { month: "short", year: "numeric" });
        });
        const values = data.map((d) => d.base_amount);
        this.chart = new Chart(this.canvasRef.el, {
            type: "bar",
            data: {
                labels,
                datasets: [
                    {
                        label: "Expenses",
                        data: values,
                        backgroundColor: "rgba(220, 53, 69, 0.7)",
                        borderColor: "rgba(220, 53, 69, 1)",
                        borderWidth: 1,
                    },
                ],
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                },
                scales: {
                    y: { beginAtZero: true },
                },
            },
        });
    }
}
