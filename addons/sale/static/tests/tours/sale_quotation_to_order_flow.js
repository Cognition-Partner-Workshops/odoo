import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_utils";
import * as tourUtils from "@sale/js/tours/tour_utils";

// Products, taxes and the salesperson are created by the Python test.
const customerName = "Tour Flow Company";

registry.category("web_tour.tours").add("sale_quotation_to_order_flow", {
    steps: () => [
        // Create a customer from the contacts action.
        {
            content: "Create a new contact",
            trigger: ".o_list_view .o_list_button_add",
            run: "click",
        },
        {
            trigger: ".o_field_widget[name=name] .o_input",
            run: `edit ${customerName}`,
        },
        {
            trigger: ".o_field_widget[name=email] .o_input",
            run: "edit tour.flow@example.com",
        },
        {
            trigger: ".o_field_widget[name=phone] .o_input",
            run: "edit +1 415 555 0127",
        },
        ...stepUtils.saveForm(),
        {
            content: "Back to the contacts",
            trigger: ".o_back_button > a",
            run: "click",
        },
        {
            trigger: ".o_searchview_input",
            run: `edit ${customerName}`,
        },
        {
            trigger: ".o_searchview_input",
            run: "press Enter",
        },
        {
            content: "Contact found in list",
            trigger: `.o_list_view .o_data_row:contains(${customerName})`,
        },
        {
            trigger: ".o_switch_view.o_kanban",
            run: "click",
        },
        {
            content: "Contact found in kanban",
            trigger: `.o_kanban_view .o_kanban_record:contains(${customerName})`,
        },
        // Quotation with two lines, then confirm it.
        stepUtils.goToUrl("/odoo/action-sale.action_quotations"),
        ...tourUtils.createNewSalesOrder(),
        ...tourUtils.selectCustomer(customerName),
        ...tourUtils.addProduct("Tour Desk"),
        {
            trigger: ".o_selected_row .o_field_widget[name=product_uom_qty] input",
            run: "edit 2",
        },
        ...tourUtils.addProduct("Tour Cabinet", 2),
        {
            content: "Total = (2 * 147 + 320) * 1.15",
            trigger: "span[name=amount_total]:contains(706.10)",
        },
        {
            trigger: ".o_form_statusbar button[name=action_confirm]",
            run: "click",
        },
        {
            trigger: ".o_statusbar_status .o_arrow_button_current:contains(Sales Order)",
        },
        // The confirmed order is listed under its salesperson.
        stepUtils.goToUrl("/odoo/action-sale.action_orders"),
        {
            trigger: ".o_searchview_dropdown_toggler",
            run: "click",
        },
        {
            trigger: ".o_group_by_menu .o-dropdown-item:contains(Salesperson)",
            run: "click",
        },
        {
            trigger: ".o_group_header:contains(Test Sales User)",
            run: "click",
        },
        {
            trigger: `.o_data_row:contains(${customerName})`,
        },
    ],
});
