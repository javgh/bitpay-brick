function request_new_invoice() {
    transition_to("#processing");
    pyObj.request_new_invoice();
}

function show_idle() {
    transition_to("#idle");
}

function show_keypad() {
    transition_to("#keypad");
}

function show_invoice(image_data) {
    $("#qrcode").attr("src", image_data)
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
    return active_div;
}

function exercise_javascript_bridge() {
    request_new_invoice();
}

var active_div = "#idle";

$(document).ready(function() {
    $("#logo").click(function() {
        show_keypad();
    });

    $("#checkmark").click(function() {
        transition_to("#idle");
    });

    $("#button_ok").click(function() {
        request_new_invoice();
    });
});


