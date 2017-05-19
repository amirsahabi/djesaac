function sendReplayRequest(songID, rowID){
    // disable submit button again
    $('#'+songID).prop('disabled', true);

    // send id to server to add to queue
    $.ajax({
        method: 'POST',
        data: {"song":songID},
        success: function(data){
            var originalRow = $('<tr class="tabledatarow">'+ $('#'+rowID).html() + '</tr>');
            var successAlert = $('<tr class="table_alert_success" id=rowID> <td colspan="4">Successfully added song to playlist</td></tr>');
            var errorAlert = $('<tr class="table_alert_error" id=rowID> <td colspan="4">Error when adding song to playlist</td></tr>');
            var alert_rep = (data.response === 'success' ? successAlert : errorAlert);
            $('#'+rowID).fadeOut('slow', function(){
                successAlert.insertAfter($(this)).hide();
                $(this).remove();
                alert_rep.fadeIn('slow', function(){});
                alert_rep.delay(1000).fadeOut('slow', function(){
                    originalRow.insertAfter(alert_rep).hide();
                    alert_rep.remove();
                    originalRow.fadeIn('slow');
                });

            });
            $('#'+songID).prop('disabled', false);
        },
        error: function(){
            var originalRow = $('<tr class="tabledatarow">'+ $('#'+rowID).html() + '</tr>');
            var errorAlert = $('<tr class="table_alert_error" id=rowID> <td colspan="4">Error when adding song to playlist</td></tr>');
            $('#'+rowID).fadeOut('slow', function(){
                errorAlert.insertAfter($(this)).hide();
                $(this).remove();
                errorAlert.fadeIn('slow', function(){});
                errorAlert.delay(1000).fadeOut('slow', function(){
                    originalRow.insertAfter(errorAlert).hide();
                    errorAlert.remove();
                    originalRow.fadeIn('slow');
                });
            });
            $('#' + songID).prop('disabled', false);
        }
    });
}

function rearrangeHistoryTable(parameters){
    //verify old song isn't bunk
    if(!(typeof parameters.oldID === 'string' && parameters.oldID.trim() === '' &&
            parameters.oldTitle === '' && parameters.oldLink === '')){
        var dataRows = $('tr.tabledatarow');
        dataRows.each(function(){
            var indexCount = $(this).find('.indexcolumn').text();
            $(this).find('.indexcolumn').text(parseInt(indexCount)+1);
        });

        // create new element
        var newRow = $(document.createElement('tr'));
        newRow.attr('class', 'tabledatarow');
        var indexColumn = $(document.createElement('td'));
        indexColumn.attr('class','indexcolumn');
        indexColumn.text('0');
        newRow.append(indexColumn);
        var titleColumn = $(document.createElement('td'));
        titleColumn.attr('class', 'titlecolumn');
        var linkRef = $(document.createElement('a'));
        linkRef.attr('id', 'table_link');
        linkRef.attr('href', parameters.oldLink);
        linkRef.text(parameters.oldTitle);
        titleColumn.append(linkRef);
        newRow.append(titleColumn);
        var replayColumn = $(document.createElement('td'));
        replayColumn.attr('class', 'replaycolumn');
        var icon = $(document.createElement('i'));
        icon.attr('class', 'material-icons');
        var playStop = $(document.createElement('span'));
        playStop.attr('class', 'play_stop');
        playStop.attr('onclick', "sendReplayRequest('"+parameters.oldID+"')");
        playStop.text('replay');
        icon.append(playStop);
        replayColumn.append(icon);
        newRow.append(replayColumn);

        //insert new element into table
        dataRows.parent().prepend(newRow);
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