function show_idle() {
    transition_to("#idle");
}

function show_invoice(url) {
    $("#iframe").attr("src", url);

    transition_to("#invoice");
}

function transition_to(replacement_div) {
    $(active_div).fadeOut("fast", function() {
        $(replacement_div).fadeIn("fast");
    });
    active_div = replacement_div;
}

function get_current_invoice() {
    if (active_div != "#invoice")
        return;

    return $("#iframe").attr("src");
}

var active_div = "#idle";
