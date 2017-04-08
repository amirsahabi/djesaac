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

function skipSong(songID){
    $('.skipsong').prop('disabled', true);

    $.ajax({
        method: 'POST',
        data : {
            "command":"next",
            "songID":songID
        },
        success: function(data){
            if(data !== 'success'){
                alert('Received error: ' + data);
            }
        },
        error: function(){
            alert("Something went wrong when submitting, try again");
            $('.skipsong').prop('disabled',false);
        }
    });
}

function startStop(){
    $('#startStop').prop('disabled', true);

    //send request to server
    $.ajax({
        method: 'POST',
        data : {
            "command":"startstop"
        },
        success: function(data){
            if(data === "success"){
                //reload page I guess?
                window.location.reload();
            } else {
                alert("Received error: " + data);
                $('#startStop').prop('disabled', false);
            }
        },
        error: function(){
            alert("Something went wrong sending request, try again");
            $('#startStop').prop('disabled',false);
        }
    })
}



$(function(){

    $(window).on('scroll', function(){
        if ( ! $(document).scrollTop()){ //top of page
            $('#nav').removeClass('shadow');
        }
        else {
            $('#nav').addClass('shadow');
        }
    });

});



$(function(){
    $("#add").click(function(){
        $("p").slideDown();
    });
});
