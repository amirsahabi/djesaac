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
                // taken care of by back end ActionHistory
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
    //check song is playing
    if($('.currently_playing').find('tr.tabledatarow').length > 0){
        //create new row
        var table = $('div.playlist').find('table');
        var newObj = $('<tr class="tabledatarow"></tr>');
        var count = table.find('tr.tabledatarow').length + 1;
        newObj.append('<td class="queueindexcolumn">'+count+"</td>");
        newObj.append('<td class="songtitlecolumn">'+'<a id="table_link" href="'+parameters.newLink+'">'+parameters.newTitle+'</a>'+"</td>");
        var remove = $('<i class="material-icons"><span class="remove" id="'+parameters.newID+'" onclick="removeSongFromQueue(\''+parameters.newID+'\')">remove_circle_outline</span></i>');
        newObj.append($("<td class=\"removebuttoncolumn\"></td>").append(remove));
        table.append(newObj);
    } else {
        var table = $('.currently_playing').find('table');
        var newObj = $('<tr class="tabledatarow"></tr>');
        var icon = parameters.currentlyPlaying ? "pause_circle_outline" : "play_circle_outline";
        var img = $('<i class="material-icons"><span class="play_stop" onclick="startStop()">'+icon+'</span></i>');
        var next = $('<i class="material-icons"><span class="skipsong" onClick="skipSong(\''+parameters.newID+'\')">skip_next</span></i>');
        var td = $('<td class="playstopnextcolumn"></td>');
        td.append(img).append(next);
        newObj.append(td);
        //newObj.append($('<td class="songtitlecolumn">'+parameters.newTitle+'</td>'));
        newObj.append($('<td class="songtitlecolumn"> <a id="table_link" href="'+parameters.newLink+'">' + parameters.newTitle + '</a> </td>'));
        //newObj.append($('<td><a id="table_link" href="'+parameters.newLink+'">Link</a></td>'));
        table.append(newObj);
    }
}

function removeSongFromQueueFromUpdate(parameters){
    var songFound = false;

    var rows = $('div.playlist').find('table').find('.tabledatarow');
    rows.each(function(){
        if(songFound){
            var index = $(this).find('td.queueindexcolumn');
            index.text(parseInt(index.text()) - 1);
        } else {
            var songTitle = $(this).find('td.songtitlecolumn');
            var songlink  = $(this).find('td.songtitlecolumn').find('a');
            var songId    = $(this).find('td.removebuttoncolumn').find('span');

            if(songTitle.text().trim() == parameters.oldTitle &&
                songlink.attr('href') == parameters.oldLink &&
                songId.attr('id') == parameters.oldID){

                $(this).remove();
                songFound = true;
            }
        }
    });
}

function stopPlayChange(parameters){
    if(parameters.currentlyPlaying == '1.0'){
        //play
        $('span.play_stop').text('pause_circle_outline');
    } else {
        //stop
        $('span.play_stop').text('play_circle_outline');
    }
}

$(window).on('scroll', function(){
    if ( ! $(document).scrollTop()){ //top of page
        $('#nav').removeClass('shadow');
    }
    else {
        $('#nav').addClass('shadow');
    }
});


