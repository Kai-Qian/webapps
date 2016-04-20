//Cite from "Learning Djngo Web Development"
//https://books.google.com/books?id=Xs_2CQAAQBAJ&pg=PA146&lpg=PA146&dq=django+follow+unfollow&source=bl&ots=tKwWI68tcK&sig=h5Nc7ny6vT6MLJFPjZS2bN2C6n0&hl=zh-CN&sa=X&ved=0ahUKEwin5s-6j_jKAhWPsh4KHYzxBvI4ChDoAQgpMAI#v=onepage&q&f=false
$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie != '') {
                //console.log(document.cookie);
                var cookies = document.cookie.split(';');
                //console.log(cookies);
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        //console.log(cookie.substring(name.length + 1));
                        //console.log(cookieValue);
                        break;
                    }
                }
            }
            return cookieValue;
        }

        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            // Only send the token to relative URLs i.e. locally.
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    }
});