///////////////////////////////////////////////////////////////////////:
// LOADS SAVED CONFIGURATION CHANGES FROM PREVIOUS USE OR OTHER CLIENTS:
///////////////////////////////////////////////////////////////////////:
function loadConfig() {
    $.ajax({
        url: '/_get_config',
        type: 'POST',
        dataType: 'json',
        success: function(response) {
            $("#mode").html(response["hvac_mode"]);
            $("#sp_value").html(response["home_setpoint"]);

            var btn_Container = document.getElementById("button-grp");
            var btns = btn_Container.getElementsByClassName("btn");
            var active_btn = document.getElementById(response["hvac_mode"]);

            // var background_type = document.getElementById();


            active_btn.className += " active";

            for (var i = 0; i < btns.length; i++) {

                if (btns[i].id != response["hvac_mode"]) {
                    btns[i].className = btns[i].className.replace(" active", "");
                };
            };
        },
        error: function(error) {
            console.log(error);
        }
    })
};
// RUNS 'loadConfig' when the window has loaded and is ready
$( window ).on( "load", loadConfig );
//////////////////////////////////////////////////////////:
// SENSOR DATA USED FOR UPDATING TEMP AND HUMIDITY DISPLAY:
//////////////////////////////////////////////////////////:
setInterval(function(){$.ajax({
    url: '/_update_thermostat',
    type: 'POST',
    success: function(response) {
        new_temp = response["temperature"]
        $("#temp").html(new_temp);
        $("#hum").html(response["humidity"]);
        $("#time_now").html(response["time_now"]);
    },
    error: function(error) {
        console.log(error);
    }
})}, 1000);
///////////////////////////////////////////:
// CONTROL BUTTON GROUP (HVAC MODE CONTROL):
///////////////////////////////////////////:
$(document).ready(function (value) {
    $('#auto').on('click', function (e) {
        this.className += " active";
        $.ajax({
            url: '/_mode_changed',
            type: "POST",
            data: "auto",
            processData: false,
            contentType: "charset=UTF-8",
            success: function(response) {
                console.log(response);
                var btn_Container = document.getElementById("button-grp");
                var btns = btn_Container.getElementsByClassName("btn");

                for (var i = 0; i < btns.length; i++) {

                    if (btns[i].id != 'auto') {
                      btns[i].className = btns[i].className.replace(" active", "");
                  };
                };
            },
            error: function(error) {
                console.log(error);
            }
        });
    });

    $('#heat').on('click', function (e) {
        this.className += " active";
        $.ajax({
            url: '/_mode_changed',
            type: "POST",
            data: "heat",
            processData: false,
            contentType: "charset=UTF-8",
            success: function(response) {
                console.log(response);

                var btn_Container = document.getElementById("button-grp");
                var btns = btn_Container.getElementsByClassName("btn");

                for (var i = 0; i < btns.length; i++) {

                    if (btns[i].id != 'heat') {
                      btns[i].className = btns[i].className.replace(" active", "");
                  };
                };
            },
            error: function(error) {
                console.log(error);
            }
        });
    });

    $('#cool').on('click', function (e) {
        this.className += " active";
        $.ajax({
            url: '/_mode_changed',
            type: "POST",
            data: "cool",
            processData: false,
            contentType: "charset=UTF-8",
            success: function(response) {
                console.log(response);

                var btn_Container = document.getElementById("button-grp");
                var btns = btn_Container.getElementsByClassName("btn");

                for (var i = 0; i < btns.length; i++) {

                    if (btns[i].id != 'cool') {
                      btns[i].className = btns[i].className.replace(" active", "");
                  };
                };
            },
            error: function(error) {
                console.log(error);
            }
        });
    });

    $('#off').on('click', function (e) {
        this.className += " active";
        $.ajax({
            url: '/_mode_changed',
            type: "POST",
            data: "off",
            processData: false,
            contentType: "charset=UTF-8",
            success: function(response) {
                console.log(response);

                var btn_Container = document.getElementById("button-grp");
                var btns = btn_Container.getElementsByClassName("btn");

                for (var i = 0; i < btns.length; i++) {

                    if (btns[i].id != 'off') {
                      btns[i].className = btns[i].className.replace(" active", "");
                  };
                };
            },
            error: function(error) {
                console.log(error);
            }
        });

        $.ajax({
            url: '/thermostat/hvac_off',
            type: "POST",
            data: "off",
            processData: false,
            contentType: "charset=UTF-8",
            success: function(response) {
                console.log(response);
            },
            error: function(error) {
                console.log(error);
            }
        });

    });
});
//////////////////////////////////////////:
// SENSOR DATA USED FOR UPDATING THE CHART:
//////////////////////////////////////////:
$(document).ready(function () {
    const config = {
        type: 'line',
        data: {
            labels: [],
            borderColor : "#444444",
            datasets: [
                {
                    label: "Temperature",
                    yAxisID: 'A',
                    backgroundColor: 'rgb(255, 99, 132)',
                    borderColor: 'rgb(233, 30, 99)',
                    fontColor: 'rgb(255, 99, 132)',
                    borderWidth: 4,
                    fontSize: 16,
                    data: [],
                    fill: false,
                },
                {
                label: "Humidity",
                    yAxisID: 'B',
                    backgroundColor: 'rgb(0, 200, 225)',
                    borderColor: 'rgb(15, 135, 150)',
                    fontColor: 'rgb(0, 200, 225)',
                    borderWidth: 4,
                    fontSize: 16,
                    data: [],
                    fill: false,
                }
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            chartArea: {
                backgroundColor: 'rgba(62, 62, 62, 1)'
            },
            title: {
                display: false,
                text: 'Real-Time Temp with Flask'
            },
            tooltips: {
                mode: 'index',
                intersect: false,
            },
            hover: {
                mode: 'nearest',
                intersect: true
            },
            legend: {
                display: false
            },
            scales: {
                xAxes: [{
                    display: true,
                    gridLines:{
                        color: "#fff",
                        lineWidth:2
                    },
                    ticks:{
                        fontColor : "#fff",
                    },
                    scaleLabel: {
                        display: false,
                        fontColor : "#fff",
                        fontSize: 16,
                        labelString: 'Time'
                    }
                }],
                yAxes: [{
                    id: 'A',
                    type: 'linear',
                    position: 'left',
                    display: true,
                    gridLines:{
                        color: "#fff",
                        lineWidth:2,
                        zeroLineColor :"#fff",
                        zeroLineWidth : 2
                    },
                    ticks:{
                        fontColor : "#fff",
                    },
                    scaleLabel: {
                        display: false,
                        fontColor : "#fff",
                        fontSize: 16,
                        labelString: 'Temperature'
                    }}, {
                    id: 'B',
                    type: 'linear',
                    position: 'right',
                    display: true,
                    ticks:{
                        fontColor : "#fff",
                    },
                    scaleLabel: {
                        display: false,
                        fontColor : "#fff",
                        fontSize: 16,
                        labelString: 'Humidity'
                    }
                }]
            }
        }
    };

    const context = document.getElementById('chart_canvas').getContext('2d');

    Chart.defaults.global.defaultFontSize = 16;
    const lineChart = new Chart(context, config);

    const source = new EventSource("/_update_chart");

    source.onmessage = function (event) {
        const data = JSON.parse(event.data);
        if (config.data.labels.length === 20) {
            config.data.labels.shift();
            config.data.datasets[0].data.shift();
            config.data.datasets[1].data.shift();
        }
        config.data.labels.push(data.time);
        config.data.datasets[0].data.push(data.temp);
        config.data.datasets[1].data.push(data.hum);
        lineChart.update();
    }
});