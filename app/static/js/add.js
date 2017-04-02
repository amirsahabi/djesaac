function onSubmit(){
    // get element for song link
    var linkField = $('#songLink');
    var linkStr   = linkField.val();

    // send link to server to add to queue
    $.ajax({
        method: 'POST',
        data: {"link":linkStr},
        success: function(data){
            alert('Succesful submission');
            //redirect
            window.location.replace(window.location.origin);
        },
        error: function(){
            alert("Something went wrong when submitting, try again");
        }
    });
}
