function loadSetpoints() {
    $.ajax({
        url: '/_get_config',
        type: 'POST',
        dataType: 'json',
        success: function(response) {
            console.log(response)
            var oHomeSP = response['home_setpoint'];
            var oAwaySP = response['away_setpoint'];
            var oSleepSP = response['sleep_setpoint'];
            var oAwake = response['awake-time'];
            if (String(oAwake).includes('PM')) {
                oAwake = String(oAwake).replace('PM','').split(':');
                oAwake[0] = parseFloat(oAwake[0]) + 12;
            } else {
                oAwake = String(oAwake).replace('AM','').split(':');
                oAwake[0] = parseFloat(oAwake[0]);
            }
            var awakeVal = (parseFloat(oAwake[0]) * 60) + parseFloat(oAwake[1]);

            var oSleep = response['sleep-time'];
            if (String(oSleep).includes('PM')) {
                oSleep = String(oSleep).replace('PM','').split(':');
                oSleep[0] = parseFloat(oSleep[0]) + 12;
            } else {
                oSleep = String(oSleep).replace('AM','').split(':');
                oSleep[0] = parseFloat(oSleep[0]);
                if (parseFloat(oSleep[0]) <= 4) {
                    oSleep[0] = parseFloat(oSleep[0]) + 24;
                }
            }

            var sleepVal = (parseFloat(oSleep[0]) * 60) + parseFloat(oSleep[1]);

            console.log(awakeVal, sleepVal)

            $('#time-range-slider').slider('values', 0, awakeVal);
            $('#time-range-slider').slider('values', 1, sleepVal);

            $( "#awake-display" ).val(response['awake-time']);
            $( "#sleep-display" ).val(response['sleep-time']);

            $("#home_temp").val(String(oHomeSP))
            $("#away_temp").val(String(oAwaySP))
            $("#sleep_temp").val(String(oSleepSP))
        },
        error: function(error) {
            console.log(error);
        }
    })
};
// RUNS 'loadConfig' when the window has loaded and is ready
$( window ).on( "load", loadSetpoints );

function sendSetpoints() {

    sFormObject = document.forms['scheduler'];
    var home = sFormObject.elements["home_temp"].value;
    var away = sFormObject.elements["away_temp"].value;
    var sleep = sFormObject.elements["sleep_temp"].value;

    var setpoints = Array[home, away, sleep];
    console.log(setpoints)
    $.ajax({
        url: '/_sp_changed',
        type: "POST",
        data: {
            home_temp: home,
            away_temp: away,
            sleep_temp: sleep
        },
        success: function(response) {
            console.log(response);
        },
        error: function(error) {
            console.log(error);
        }
    });
};
// NUMBER SPINNERS
// (function($) {
//     $.fn.spinner = function() {
//     this.each(function() {
//     var el = $(this);
    
//     // add elements
//     el.wrap('<span class="spinner"></span>');     
//     el.before('<span class="sub">-</span>');
//     el.after('<span class="add">+</span>');
    
//     // substract
//     el.parent().on('click', '.sub', function () {
//     if (el.val() > parseInt(el.attr('min')))
//     el.val( function(i, oldval) { return (+(oldval)-.5); });
//     });
    
//     // increment
//     el.parent().on('click', '.add', function () {
//     if (el.val() < parseInt(el.attr('max')))
//     el.val( function(i, oldval) { return (+(oldval)+.5); });
//     });
//         });
//     };
// })(jQuery);
    
// $('input[type=number]').spinner();

// DOUBLE SLIDER:
$( function handleSlider() {
    // var handle1 = $( "#custom-handle-1" );
    // var handle2 = $( "#custom-handle-2" );

    $( "#time-range-slider" ).slider({
    range: true,
    min: 240,
    max: 1680,
    step: 15,
    values: [480, 1320],
    // create: function() {
    //     handle1.text( $( this ).slider( "values", 0 ) );
    //     handle2.text( $( this ).slider( "values", 1 ) );
    //   },
    start: function( event, ui ) {
    },
    slide: function( event, ui ) {

        var am_pm_1 = 'AM';
        var am_pm_2 = 'PM';

        if (ui.values[0] >= 720) {
            am_pm_1 = 'PM'
        } else { am_pm_1 = 'AM' };

        if (ui.values[1] >= 720) {
            am_pm_2 = 'PM'
        } else { am_pm_2 = 'AM' };

        if (ui.values[0] > 780 && ui.values[0] < 1440) {
            var hour_1 = Math.floor((ui.values[ 0 ] - 720) / 60);
            var min_1 = (ui.values[ 0 ] - ((hour_1 + 12) * 60));
        } else if (ui.values[0] >= 1440) {
            var hour_1 = Math.floor((ui.values[ 0 ] - 1440) / 60);
            var min_1 = (ui.values[ 0 ] - ((hour_1 + 24) * 60));
            am_pm_1 = 'AM';
        } else {
            var hour_1 = Math.floor(ui.values[ 0 ] / 60);
            var min_1 = (ui.values[ 0 ] - (hour_1 * 60));
        } 
        if (min_1 === 0) {min_1 = '00'}

        if (ui.values[1] > 780 && ui.values[1] <= 1440) {
            var hour_2 = Math.floor((ui.values[ 1 ] - 720) / 60);
            var min_2 = (ui.values[ 1 ] - ((hour_2 + 12) * 60));
            if (ui.values[1] === 1440) {
                am_pm_2 = 'AM';
            }
        } else if (ui.values[1] > 1440) {
            var hour_2 = Math.floor((ui.values[ 1 ] - 1440) / 60);
            var min_2 = (ui.values[ 1 ] - ((hour_2 + 24) * 60));
            am_pm_2 = 'AM'
        } else {
            var hour_2 = Math.floor(ui.values[ 1 ] / 60);
            var min_2 = (ui.values[ 1 ] - (hour_2 * 60));
        }
        if (min_2 === 0) {min_2 = '00'}

        $( "#awake-display" ).val(hour_1 + ":" + min_1 + am_pm_1);
        $( "#sleep-display" ).val(hour_2 + ":" + min_2 + am_pm_2);
    }
    });

    var hour_1 = Math.floor($( "#time-range-slider" ).slider( "values", 0 ) / 60);
    var min_1 = $( "#time-range-slider" ).slider( "values", 0 ) - (hour_1 * 60);
    if (min_1 === 0) {min_1 = '00'}
    var hour_2 = Math.floor($( "#time-range-slider" ).slider( "values", 1 ) / 60);
    var min_2 = $( "#time-range-slider" ).slider( "values", 1 ) - (hour_2 * 60);
    if (min_2 === 0) {min_2 = '00'}

} );


// NEW NUMBER SPINNER
$(function(){

    $("#home_spinner").htmlNumberSpinner();
    $("#away_spinner").htmlNumberSpinner();
    $("#sleep_spinner").htmlNumberSpinner();
  
  });
