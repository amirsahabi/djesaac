function getAndDisplaySettings(){
    //send get settings request
    $.ajax({
        url: '/settings/',
        method: 'GET',
        success: function(data){
            if(data.response === 'success'){
                //fill out fields and display
                $('input#board-src').val(data.board.trim());
                $('input#red-src').val(data.red.trim());
                $('input#blue-src').val(data.blue.trim());
                $('input#green-src').val(data.green.trim());
                $('input#latency').val(data.latency);
                $('input#autoplay').attr('checked', data.autoplay == true);
                $('div.modal').css('display', 'block');
            }
        }
    });
}

function saveSettings(){
    // get settings
    var board = $('input#board-src').val();
    var red = $('input#red-src').val();
    var blue = $('input#blue-src').val();
    var green = $('input#green-src').val();
    var latency = $('input#latency').val();
    var autoplay = $('input#autoplay').is(':checked');

    //send request
    $.ajax({
        url: '/settings/',
        method: 'POST',
        data :{
            'board' : board,
            'red' : red,
            'blue' : blue,
            'green' : green,
            'latency' : latency,
            'autoplay' : autoplay
        },
        success : function(data){
            var $elem = $("#submit-settings-change"),
                x = 2000,
                originalColor = $elem.css("color");
            if(data.response === 'success'){
                console.log("in here");


                $elem.css("color", "#148652");
                setTimeout(function(){
                    $elem.css("color", originalColor);
                }, x);
            }
            else{
                console.log("in err");


                $elem.css("color", "#FF4E4C");
                setTimeout(function(){
                    $elem.css("color", originalColor);
                }, x);
            }
            getAndDisplaySettings();
        },
        error: function(){
            var $elem = $("#submit-settings-change"),
                x = 2000,
                originalColor = $elem.css("color");

            $elem.css("color", "#FF4E4C");
            setTimeout(function(){
                $elem.css("color", originalColor);
            }, x);

            getAndDisplaySettings();
        }

    })
}