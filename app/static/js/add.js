function onSubmit(){

    // disable submit button again
    $('#submitButton').prop('disabled', true);

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
                alert('Successful submission');
                //redirect
                window.location.href = (window.location.origin);
            } else if(data.response === 'failure') {
                alert('Received error: ' + data.error + '. Try again');
                $('#submitButton').prop('disabled', false);
            }
        },
        error: function(){
            alert("Something went wrong when submitting, try again");
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
