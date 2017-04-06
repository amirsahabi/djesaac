function removeSongFromQueue(songID){

    // disable submit button again
    $('#'+songID).prop('disabled', true);

    // send id to server to add to queue
    $.ajax({
        method: 'POST',
        data: {
            "command":"remove",
            "songID":songID
        },
        success: function(data){
            if(data === 'success'){
                alert('Successful submission');
                window.location.href = (window.location.origin);
            } else {
                alert('Received error: ' + data);
            }
            $('#'+songID).prop('disabled', false);
        },
        error: function(){
            alert("Something went wrong when submitting, try again");
            $('#' + songID).prop('disabled', false);
        }
    });
}
