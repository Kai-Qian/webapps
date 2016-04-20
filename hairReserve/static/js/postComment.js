/**
 * Created by willQian on 2016/2/19.
 */
var postID;
$(document).ready(function () {
    postComment();
});

function postComment() {
    $('#commentModal form button').click(function () {//don't use .submit, otherwise the form will be submitted
        $.ajax({
            type: "POST",
            data: $('#commentModal form').serialize(),
            url: "/postcomment/",
            dataType: "html",
            cache: false,
            success: function (html, textStatus) {
                console.log("dddddddddddddd");
                $('#comments').replaceWith(html);
                $('#commentModal').modal('hide');
                $('#commentModal form')[0].reset();
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                alert("ERROR2 !!");
                console.log("sssssssssssssssss");
                $('#commentModal form').replaceWith('Your comment was unable to be posted at this time.  We apologise for the inconvenience.');
            }
        });
    });
}

//function getPost(tmp) {
//    postID = tmp.id;
//    console.log(postID);
//}

//function setPost() {
//    document.getElementById("tmp").value = postID;
//    console.log("hahahahahhahaha");
//}