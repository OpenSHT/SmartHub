$(document).ready(function (value) {

    $('#add_device').on('click', function (e) {
        var add_Room_Form = document.getElementById("room_form");

        if (add_Room_Form.style.display === "block") {
            add_Room_Form.style.display = "none";
        } else {
            add_Room_Form.style.display = "block";
        }
        console.log(add_Room_Form.style.display)
    });

});

function getDevices(value){$.ajax({
    url: '/_load_bt_sensors',
    type: 'POST',
    success: function(response) {
        // console.log(response)
        var container = document.createElement("DIV");   // Create a <div> element
        container.className = "row device_block";
        container.style = "margin-top:30px;"
        var name_text = document.createElement("DIV");   // Create a <div> element
        name_text.className = "col-20";
        name_text.innerHTML = "Thermostat";
        var mac = document.createElement("DIV");
        mac.className = "col-20";
        mac.innerHTML = "<p>local</p>";
        var prior = document.createElement("DIV");
        prior.className = "col-20 local_priority";  // Create an element we can later update with the sensor values
        prior.id = "local_priority"
        var edit_prior = document.createElement("INPUT");
        edit_prior.setAttribute("type", "text");
        edit_prior.setAttribute("placeholder", "1-4");
        edit_prior.style = "display:none;width: 20%;";

        var sens_values = document.createElement("DIV");
        sens_values.className = "col-20 local_values";  // Create an element we can later update with the sensor values

        var edit_btns = document.createElement("DIV");
        edit_btns.className = "col-20";
        edit_btns.innerHTML = "<a href='#' id='edit_local' class='edit_btn'><i class='fas fa-edit'></i></a>";

        var sub = document.createElement('INPUT');
        sub.setAttribute("type", "submit");
        sub.style = "display:none;";

        container.appendChild(name_text);
        container.appendChild(mac);
        container.appendChild(prior);
        container.appendChild(edit_prior);
        container.appendChild(sens_values);
        container.appendChild(edit_btns);
        container.appendChild(sub);

        document.getElementById("device_header").appendChild(container);

        $('#edit_local').on('click', function (e) {
            this.style = "display:none;";
            var prior = document.getElementById('local_priority')
            prior.style = "display:none;";
            edit_prior.style = "display:inline-block;width:20%;float:left;margin:0;";
            sub.style = "display:inline-block;float:left;margin:0;";
        });

        for(var key in response) {
            console.log(response[key])
            var device_data = response[key];
            mac_addr = device_data[0];
            priority = device_data[1];
            if (priority === 1) { priority = 'Low'; }
            else if (priority === 2) { priority = 'Medium'; }
            else if (priority === 3) { priority = 'High'; }
            else if (priority === 4) { priority = 'Highest'; }

            var container = document.createElement("DIV");   // Create a <div> element
            container.className = "row device_block";
            // container.style = "margin-top:30px;"
            var name_text = document.createElement("DIV");   // Create a <div> element
            name_text.className = "col-20";
            name_text.innerHTML = key;
            var mac = document.createElement("DIV");
            mac.className = "col-20";
            mac.innerHTML = "<p'>" + mac_addr + "</p>";
            var prior = document.createElement("DIV");
            prior.className = "col-20";
            prior.innerHTML = "<p'>" + priority + "</p>";
            
            var sens_values = document.createElement("DIV");
            sens_values.className = "col-20 " + key;  // Create an element we can later update with the sensor values

            var edit_btns = document.createElement("DIV");
            edit_btns.className = "col-20";
            edit_btns.innerHTML = "<a href='#' id='edit_" + key + "' class='edit_btn'><i class='fas fa-edit'></i></a> <a href='#' id='remove_" + key + "' class='remove_btn edit_btn'><i class='fas fa-minus'></i></a>";

            container.appendChild(name_text);
            container.appendChild(mac);
            container.appendChild(prior);
            container.appendChild(sens_values);
            container.appendChild(edit_btns);
            
            document.getElementById("device_header").appendChild(container);
          }
        
    },
    error: function(error) {
        console.log(error);
    }
})};

$( window ).on( "load", getDevices );

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
                if (new_prior === 1) { new_prior = 'Low'; }
                else if (new_prior === 2) { new_prior = 'Medium'; }
                else if (new_prior === 3) { new_prior = 'High'; }
                else if (new_prior === 4) { new_prior = 'Highest'; }
                $(".local_priority").html(new_prior);
            }
        }
    },
    error: function(error) {
        console.log(error);
    }
})}, 1000);