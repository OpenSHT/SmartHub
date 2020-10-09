$(document).ready(function (value) {

    $('#add_device').on('click', function (e) {
        var add_Room_Form = document.getElementById("room_form");

        if (add_Room_Form.style.display === "block") {
            add_Room_Form.style.display = "none";
        } else {
            add_Room_Form.style.display = "block";
        }
        // console.log(add_Room_Form.style.display)
    });

});

function getDevices(value){$.ajax({
    url: '/_load_bt_sensors',
    type: 'POST',
    success: function(response) {
        // console.log(response)
        const container = document.createElement("FORM");   // Create a <form> element
        container.className = "row device_block";
        container.id = "device_edit_form";
        container.setAttribute("action", '#');
        container.setAttribute("method", "post");
        container.setAttribute("onsubmit", "sendEditedDevice()")
        // container.style = "margin-top:30px;";
        const name_text = document.createElement("DIV");   // Create a <div> element
        name_text.className = "col-20 sens_name";
        name_text.innerHTML = "Thermostat";
        const mac = document.createElement("DIV");
        mac.className = "col-20";
        mac.innerHTML = "<p>local</p>";
        const prior = document.createElement("DIV");
        prior.className = "col-20 local_priority priority";  // Create an element we can later update with the sensor values
        prior.id = "prior_Local";
        const edit_prior = document.createElement("INPUT");
        edit_prior.setAttribute("type", "text");
        edit_prior.setAttribute("name", "local_priority");
        edit_prior.setAttribute("placeholder", "1-4");
        edit_prior.style = "display:none;";
        edit_prior.className = "col-20 edit_prior room_input";
        edit_prior.id = "edit_prior_local";

        const sens_values = document.createElement("DIV");
        sens_values.className = "col-20 local_values";  // Create an element we can later update with the sensor values

        const edit_btns = document.createElement("DIV");
        edit_btns.className = "col-20";
        edit_btns.innerHTML = "<a href='#' id='edit_local' class='edit_btn'><i class='fas fa-edit'></i></a>";

        const sub = document.createElement('INPUT');
        sub.setAttribute("type", "submit");
        sub.style = "display:none;";
        sub.className = "col-20 room_input room_sub";
        sub.id = "submit_local";

        container.appendChild(name_text);
        container.appendChild(mac);
        container.appendChild(prior);
        container.appendChild(edit_prior);
        container.appendChild(sens_values);
        container.appendChild(edit_btns);
        container.appendChild(sub);

        document.getElementById("device_header").appendChild(container);

        $('#edit_local').on('click', function () {
            this.style = "display:none;";
            const sub = document.getElementById("submit_local");
            sub.style = "display:block;float:left;";
            const prior = document.getElementById('prior_Local');
            prior.style = "display:none;";
            const edit_prior = document.getElementById("edit_prior_local");
            edit_prior.style = "display:block;float:left;";
            
        });
        
        var device_list = [];
        
        for(var key in response) {
            console.log(key, response[key]);
            device_list.push(key);
        }
        var arrayLength = device_list.length;

        for (var i = 0; i < arrayLength; i++) {
            device_data = response[device_list[i]];
            mac_addr = device_data[0];
            priority = device_data[1];
            if (priority === 1) { priority = 'Low - 1'; }
            else if (priority === 2) { priority = 'Medium - 2'; }
            else if (priority === 3) { priority = 'High - 3'; }
            else if (priority === 4) { priority = 'Highest - 4'; }

            const name_text = document.createElement("DIV");   // Create a <div> element
            name_text.className = "col-20 sens_name";
            name_text.innerHTML = device_list[i];
            const mac = document.createElement("DIV");
            mac.className = "col-20";
            mac.innerHTML = "<p'>" + mac_addr + "</p>";
            const prior = document.createElement("DIV");
            prior.className = "col-20 priority";
            prior.innerHTML = priority;
            prior.id = "prior_" + device_list[i];
            const edit_prior = document.createElement("INPUT");
            edit_prior.setAttribute("type", "text");
            edit_prior.setAttribute("name", device_list[i] + "_priority");
            edit_prior.setAttribute("placeholder", "1-4");
            edit_prior.style = "display:none;";
            edit_prior.className = "col-20 edit_prior room_input";
            edit_prior.id = "edit_prior_" + device_list[i];

            const sens_values = document.createElement("DIV");
            sens_values.className = "col-20 " + device_list[i];  // Create an element we can later update with the sensor values

            const edit_btns = document.createElement("DIV");
            edit_btns.className = "col-20";
            edit_btns.innerHTML = "<a href='#' id='edit_" + device_list[i] + "' class='edit_btn'><i class='fas fa-edit'></i></a> <a href='#' id='remove_" + device_list[i] + "' class='remove_btn edit_btn'><i class='fas fa-minus'></i></a>";

            const sub = document.createElement('INPUT');
            sub.setAttribute("type", "submit");
            sub.style = "display:none;";
            sub.className = "col-20 room_input room_sub";
            sub.id = "submit_" + device_list[i];

            container.appendChild(name_text);
            container.appendChild(mac);
            container.appendChild(prior);
            container.appendChild(edit_prior);
            container.appendChild(sens_values);
            container.appendChild(edit_btns);
            container.appendChild(sub);
            
            document.getElementById("device_header").appendChild(container);

            // console.log('#edit_' + device_list[i])
            const dev = device_list[i]
            $('#edit_' + device_list[i]).on('click', function () {
                // console.log('remove_' + dev)
                this.style = "display:none;";
                const remove_btn = document.getElementById('remove_' + dev);
                remove_btn.style = "display:none;";
                const sub = document.getElementById("submit_" + dev);
                sub.style = "display:block;float:left;";
                const prior = document.getElementById('prior_' + dev);
                prior.style = "display:none;";
                const edit_prior = document.getElementById("edit_prior_" +dev);
                edit_prior.style = "display:block;float:left;";
            });

            $('#remove_' + device_list[i]).on('click', function () {
                var answer = window.confirm("Are you sure want to remove this device?");
                if (answer) {
                    $.ajax({
                        url: '/_remove_device',
                        type: "POST",
                        data: {
                            device: dev
                        },
                        success: function(response) {
                            console.log("Removed");
                            window.location.reload();
                            // return false;
                        },
                        error: function(error) {
                            console.log(error);
                        }
                    });
                }
                else {
                    console.log("Device was not removed")
                }
            }); 
        }; 
    },
    error: function(error) {
        console.log(error);
    }
})};

$( window ).on( "load", getDevices );

function sendEditedDevice() {
    inputs = document.getElementsByClassName("edit_prior");
    console.log(inputs)
    var inputLength = inputs.length;
    for (var t = 0; t < inputLength; t++) {
        if (inputs[t].value === "4") {
            priorities = document.getElementsByClassName("priority");
            console.log(priorities)
            var listLength = priorities.length;
            for (var p = 0; p < listLength; p++) {
                // console.log(priorities[p].innerHTML)
                if (priorities[p].innerHTML === "Highest - 4") {
                    room_name = priorities[p].id.replace('prior_', '');
                    alert("WARNING: This will lower the priority of the " + room_name)
                }
            }
        }
    }
    // sFormObject = document.getElementById("edit_prior_local");
    // console.log(sFormObject.value);
    // if (sFormObject.value === '4') {
    //     priorities = document.getElementsByClassName("priority");
    //     console.log(priorities)
    //     var listLength = priorities.length;
    //     for (var p = 0; p < listLength; p++) {
    //         // console.log(priorities[p].innerHTML)
    //         if (priorities[p].innerHTML === "Highest - 4") {
    //             room_name = priorities[p].id.replace('prior_', '')
    //             alert("WARNING: This will lower the priority of the " + room_name)
    //         }
    //     }
    //     // alert("trying to set highest...")
    // }
    
};
// function sendNewDevice() {

//     sFormObject = document.forms['scheduler'];
//     var home = sFormObject.elements["home_temp"].value;
//     var away = sFormObject.elements["away_temp"].value;
//     var sleep = sFormObject.elements["sleep_temp"].value;
// };



//////////////////////////////////////////////////////////:
// SENSOR DATA USED FOR UPDATING TEMP AND HUMIDITY DISPLAY:
//////////////////////////////////////////////////////////:
setInterval(function(){$.ajax({
    url: '/_update_rooms',
    type: 'POST',
    success: function(response) {
        for(var key in response) {
            new_name = key;
            new_temp = response[key][0];
            new_hum = response[key][1];
            $("."+key).html(new_temp + "C | " + new_hum + "%");
            if (key === 'local_values') {
                new_prior = response[key][2];
                if (new_prior === 1) { new_prior = 'Low - 1'; }
                else if (new_prior === 2) { new_prior = 'Medium - 2'; }
                else if (new_prior === 3) { new_prior = 'High - 3'; }
                else if (new_prior === 4) { new_prior = 'Highest - 4'; }
                $("#prior_Local").html(new_prior);
            }
        }
    },
    error: function(error) {
        console.log(error);
    }
})}, 1000);