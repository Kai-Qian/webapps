/**
 * Created by willQian on 2016/2/7.
 */
//function size(textInput) {
//
//    var maxNum = 170;
//
//    if (textInput.value.length <= maxNum) {
//        var str = textInput.value.length;
//        document.getElementById("span").innerHTML = str.toString();
//    } else {
//        var content = textInput.value;
//        document.getElementById("span").innerHTML = "160";
//        textInput.value = content.substring(0, 160);
//        textInput.focus();
//    }
//
//}

//function count(textInput) {
//
//    var maxNum = 400;
//
//    if (textInput.value.length <= maxNum) {
//        var str = textInput.value.length;
//        document.getElementById("span2").innerHTML = str.toString();
//    } else {
//        var content = textInput.value;
//        document.getElementById("span2").innerHTML = "400";
//        textInput.value = content.substring(0, 400);
//        textInput.focus();
//    }
//
//}

//$(document).ready(function () {
//    followOrUnfollow();
//});
//Cite from "Learning Djngo Web Development"
//https://books.google.com/books?id=Xs_2CQAAQBAJ&pg=PA146&lpg=PA146&dq=django+follow+unfollow&source=bl&ots=tKwWI68tcK&sig=h5Nc7ny6vT6MLJFPjZS2bN2C6n0&hl=zh-CN&sa=X&ved=0ahUKEwin5s-6j_jKAhWPsh4KHYzxBvI4ChDoAQgpMAI#v=onepage&q&f=false
function followOrUnfollow(tmp) {
    //$(".follow-btn").click(function () {
        console.log("aaaaaaaaaa");
        var barbershopname = $(tmp).attr('barbershopname');
        var follow = $(tmp).attr('value') != "True";
        $.ajax({
            type: "POST",
            url: "/follow/" + barbershopname + "/",
            data: {barbershopname: barbershopname, follow: follow},
            success: function (html, textStatus) {

                $('#followButton').replaceWith(html);
                //window.location.reload();
            },
            error: function () {
                alert("ERROR !!");
            }
        });
    //});
}