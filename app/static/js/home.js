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
            if(data.response === 'success'){
                alert('Successful submission');
                window.location.href = (window.location.origin);
            } else if(data.response === "failure") {
                alert('Received error: ' + data.error);
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
            if(data.response !== 'success'){
                alert('Received error: ' + data.error);
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
            if(data.response === "success"){
                //reload page I guess?
                window.location.reload();
            } else if(data.response === "failure") {
                alert("Received error: " + data.error);
                $('#startStop').prop('disabled', false);
            }
        },
        error: function(){
            alert("Something went wrong sending request, try again");
            $('#startStop').prop('disabled',false);
        }
    })
}

function reArrangeQueueTable(parameters){
    //get rows
    var currentlyPlayingRow = $('.currently_playing').find('tr.tabledatarow');
    //check there is a song now playing
    if(currentlyPlayingRow.length > 0){
        if(typeof parameters.newID === 'string' && parameters.newID.trim() === '' &&
        parameters.newTitle == '' && parameters.newLink == ""){
            //no next song, just remove the column
            currentlyPlayingRow.remove();
        } else {
            //acocomodate next song
            currentlyPlayingRow.find('.skipsong').attr('onclick', "skipSong('"+parameters.newID+"')");
            currentlyPlayingRow.find('.songtitlecolumn').text(parameters.newTitle);
            currentlyPlayingRow.find('#table_link').attr('href', parameters.newLink);
        }
    }
    var playlistRows = $('.playlist').find('tr.tabledatarow');
    if(playlistRows.length > 0){
        $(playlistRows[0]).remove();
        // playlistRows = $('.playlist').find('tr.tabledatarow');
        playlistRows.each(function(){
            var indexNum = $(this).find('.queueindexcolumn').text();
            $(this).find('.queueindexcolumn').text(parseInt(indexNum)-1);
        })
    }
}

function addNewSongToQueue(parameters){
    //create new row
    var newObj = $('<tr class="tabledatarow"></tr>');
    newObj.append('<td class="queueindexcolumn">'+parameters.count+"</td>");
    newObj.append('<td class="songtitlecolumn">'+parameters.newTitle+"</td>");
    var link = $('<a id="table_link" href="'+parameters.newLink+'">Link</a>');
    newObj.append($("<td></td>").append(link));
    var remove = $('<i class="material-icons"><span class="remove" onclick="removeSongFromQueue("'+parameters.newID+'")">remove_circle_outline</span></i>');
    newObj.append($("<td></td>").append(remove));
    var table = $('div.playlist').find('table');
    table.append(newObj);
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
