function onSubmit(){

    // disable submit button again
    $('#submitButton').prop('disabled', true);

    // get element for song link
    var linkField = $('#songLink');
    var linkStr   = linkField.val();

    // send link to server to add to queue
    $.ajax({
        method: 'POST',
        data: {"link":linkStr},
        success: function(data){
            if(data === 'success'){
                alert('Succesful submission');
                $('#submitButton').prop('disabled', false);
                //redirect
                window.location.href = (window.location.origin);
            } else {
                alert('Received error: ' + data + '. Try again');
            }
        },
        error: function(){
            alert("Something went wrong when submitting, try again");
        }
    });
}
