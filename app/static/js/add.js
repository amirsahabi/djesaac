function onSubmit(){

    // disable submit button again
    $('#submitButton').prop('disabled', true);
    $('#songLink').addClass('hide');
    $('#submitButton').addClass('hide');

    $("#loadingSongLink").fadeIn();
    var originalText = $("#loadingSongLink").text(),
        i  = 0;
    setInterval(function() {
        $("#loadingSongLink").append(".");
        i++;
        if(i == 4)
        {
            $("#loadingSongLink").html(originalText);
            i = 0;
        }
    }, 500);

    // get element for song link
    var linkField = $('#songLink');
    var linkStr   = linkField.val();

    // send link to server to add to queue
    $.ajax({
        url: '/add/',
        method: 'POST',
        data: {"link":linkStr},
        success: function(data){
            var alert_res = (data.response === 'success' ? $("#add_suc") : $("#add_fail"));
            $("#loadingSongLink").fadeOut(500).promise().done(function(){
                alert_res.fadeIn().promise().done(function(){
                    setTimeout(function () {
                        alert_res.fadeOut().promise().done(function(){
                            document.getElementById("songLink").value = "";
                            $('#songLink').removeClass('hide');
                            $('#submitButton').removeClass('hide');
                        });

                    }, 2000);
                });
            });

            $('#submitButton').attr('disabled', false);

        },
        error: function(){
            $("#loadingSongLink").fadeOut(500).promise().done(function(){
                $("#add_fail").fadeIn().delay(1000).fadeOut().promise().done(function(){
                    setTimeout(function () {
                        document.getElementById("songLink").value = "";
                        $('#songLink').removeClass('hide');
                        $('#submitButton').removeClass('hide');
                    }, 500);
                });
            });
            $('#submitButton').attr('disabled', false);
        }
    });
}

$(document).ready(function () {
    $(document).on("keyup", "#songLink", function (e) {
        if(e.keyCode == 13){
            $("#submitButton").click();
        }
    });
});
