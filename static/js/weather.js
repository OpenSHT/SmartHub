//////////////////////////////////////////////////////////:
// SENSOR DATA USED FOR UPDATING TEMP AND HUMIDITY DISPLAY:
//////////////////////////////////////////////////////////:
function upd_weather() {
    $.ajax({
        url: '/_update_weather',
        type: 'POST',
        dataType: 'json',
        success: function(response) {
            console.log(response)
            $("#owm_city").html(response["city"]);
            $("#owm_cc").html(response["cc"]);
            $("#temp_out").html(response["temp"]);
            $("#temp_max_out").html(response["temp_max"]);
            $("#temp_min_out").html(response["temp_min"]);
            $("#temp_feel_out").html(response["temp_feel"]);
            $("#hum_out").html(response["humidity"]);
            $("#wind_spd").html(response["wind_speed"]);
            $("#pressure_out").html(response["pressure"]);
            $("#weather_status").html(response["status"]);
            $("#weather_dets").html(response["detailed_status"]);

            const source = "http://openweathermap.org/img/wn/" + response["icon"] + "@4x.png";
            var weather_icon = document.getElementById("weather_icon");
            weather_icon.src = source;
        },
        error: function(error) {
            console.log(error);
        }
    })
};
// Run every 5 minutes
setInterval( upd_weather, 300000 );
// Run at startup also so we dont have to wait...
$( window ).on( "load", upd_weather );

// DRAW A CIRCLE
// var weather_canvas = document.getElementById('icon_back');
// var weather_context = weather_canvas.getContext('2d');
// var centerX = 0;
// var centerY = 0;
// var radius = 45;
// // save state
// weather_context.save();
// // translate context
// weather_context.translate(weather_canvas.width / 2, weather_canvas.height / 2);
// // scale context horizontally
// weather_context.scale(1, 1);
// // draw circle which will be stretched into an oval
// weather_context.beginPath();
// weather_context.arc(centerX, centerY, radius, 0, 2 * Math.PI, false);

// // restore to original state
// weather_context.restore();

// // apply styling
// weather_context.fillStyle = '#222222';
// weather_context.fill();
// weather_context.lineWidth = 1;
// weather_context.strokeStyle = '#fafafa';
// weather_context.stroke();