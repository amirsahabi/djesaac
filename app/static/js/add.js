function onSubmit(){

    // disable submit button again
    $('#submitButton').prop('disabled', true);
    $('#songLink').addClass('hide');
    $('#submitButton').addClass('hide');

    $("#loadingSongLink").fadeIn();
    var originalText = $("#loading").text(),
        i  = 0;
    setInterval(function() {
        $("#loading").append(".");
        i++;
        if(i == 4)
        {
            $("#loading").html(originalText);
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
            if(data.response === 'success'){
                $("#loadingSongLink").fadeOut(500).promise().done(function(){
                    $("#add_suc").fadeIn().promise().done(function(){
                        setTimeout(function () {
                            window.location.href = (window.location.origin);
                        }, 2000); //redirect in 2sec
                    });
                });

            } else if(data.response === 'failure') {
                $("#loadingSongLink").fadeOut(500).promise().done(function(){
                    $("#add_fail").fadeIn().delay(1000).fadeOut().promise().done(function(){
                        setTimeout(function () {
                            $('#songLink').removeClass('hide');
                            $('#submitButton').removeClass('hide');
                        }, 500);
                    });
                });
                $('#submitButton').prop('disabled', false);
            }
        },
        error: function(){
            $("#loadingSongLink").fadeOut(500).promise().done(function(){
                $("#add_fail").fadeIn().delay(1000).fadeOut().promise().done(function(){
                    setTimeout(function () {
                        $('#songLink').removeClass('hide');
                        $('#submitButton').removeClass('hide');
                    }, 500);
                });
            });
            $('#submitButton').prop('disabled', false);
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


