function sendReplayRequest(songID, rowID){
    // disable submit button again
    $('#'+songID).prop('disabled', true);

    // send id to server to add to queue
    $.ajax({
        method: 'POST',
        data: {"song":songID},
        success: function(data){
            if(data.response === 'success'){
                var successAlert = $('<tr class="alert_success" id=rowID> <td colspan="4">Successfully added song to playlist</td></tr>');
                var originalRow = $('<tr class="tabledatarow">'+ $('#'+rowID).html() + '</tr>');

                $('#'+rowID).fadeOut('slow', function(){
                    successAlert.insertAfter($(this)).hide();
                    $(this).remove();
                    successAlert.fadeIn('slow', function(){});
                    successAlert.delay(1000).fadeOut('slow', function(){
                        originalRow.insertAfter(successAlert).hide();
                        successAlert.remove();
                        originalRow.fadeIn('slow');
                    });

                });

            } else if(data.response === 'failure'){
                var errorAlert = $('<tr class="alert_error" id=rowID> <td colspan="4">Error when adding song to playlist</td></tr>');
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
            }
            $('#'+songID).prop('disabled', false);



        },
        error: function(){
            var errorAlert = $('<tr class="alert_error" id=rowID> <td colspan="4">Error when adding song to playlist</td></tr>');
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
        titleColumn.text(parameters.oldTitle);
        newRow.append(titleColumn);
        var linkColumn = $(document.createElement('td'));
        linkColumn.attr('class', 'linkcolumn');
        var linkRef = $(document.createElement('a'));
        linkRef.attr('id', 'table_link');
        linkRef.attr('href', parameters.oldLink);
        linkRef.text('Link');
        linkColumn.append(linkRef);
        newRow.append(linkColumn);
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
        newRow.append(replayColumn);;

        //insert new element into table
        dataRows.parent().prepend(newRow);
    }
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
