function show_idle() {
    transition_to("#idle");
}

function show_invoice(image_data) {
    transition_to("#invoice");
}

function show_paid() {
    transition_to("#paid");
}

function transition_to(replacement_div) {
    $(active_div).fadeOut("fast", function() {
        $(replacement_div).fadeIn("fast");
    });
    active_div = replacement_div;
}

function get_active_div() {
    return active_div
}

var active_div = "#idle";
