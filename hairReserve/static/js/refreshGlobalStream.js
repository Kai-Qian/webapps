/**
 * Created by willQian on 2016/2/19.
 */
$(document).ready(function() {
    homeRefresh()
    sendReminder()
});

function homeRefresh() {
    var barbershop_name = $(".barbershop_name").data('barbershop_name');
    $.ajax({
        type: "POST",
        url: "/getallcomments/",
        data: {barbershop_name: barbershop_name},
        success: function (html, textStatus) {
            $('#comments').replaceWith(html);
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            //alert("ERROR1 !!");
        }
    });
}

function sendReminder() {
    $.ajax({
        type: "GET",
        data: {},
        url: "/sendReminder/",
        //dataType: "html",
        success: function (html, textStatus) {
            console.log("Email sent.")
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            //alert("ERROR1 !!");
        }
    });
}

// causes the sendRequest function to run every 5 seconds
window.setInterval(homeRefresh, 5000);
window.setInterval(sendReminder, 70000);
