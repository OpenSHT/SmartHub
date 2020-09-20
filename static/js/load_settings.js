function loadSettings() {
    $.ajax({
        url: '/_get_config',
        type: 'POST',
        dataType: 'json',
        success: function(response) {
            console.log(window.location.href);

            var oImageType = response['back-type'];
            var oBackFile = response["back-file"];
            var oImagePos = response["back-pos"];
            var oBackColor = response["back-color"];
            var oIntTheme = response["int-theme"];
            var oIntUnit = response["int-unit"];
            var oSearchList = response["result-list"]

            // Do stuff if we land on the General Settings page:
            if (String(window.location.href).includes('/settings')) {

                gsFormObject = document.forms['general'];

                gsImageType = gsFormObject.elements["image-type"]; 
                gsImagePos = gsFormObject.elements["image-position"];
                gsIntTheme = gsFormObject.elements["interface-theme"];
                gsIntUnit = gsFormObject.elements["interface-unit"];
                gsBackColor = gsFormObject.elements["color-chooser"];
                gsSearchDropD = gsFormObject.elements["search-results"];
                gsSearchBox = document.getElementById('location-search');
                gsSearchIcon = document.getElementsByClassName('fa-search-location');
                // gsBackFile = gsFormObject.elements["file-chooser"];
                console.log(oSearchList.length)
                if (oSearchList.length != 0) {
                    gsSearchDropD.style.display = 'block';
                    gsSearchBox.style.display = 'none';
                    gsSearchIcon[0].style.display = 'none';

                    for (var i = 0; i < oSearchList.length; i++) {
                        var opt = document.createElement('option');
                        opt.value = oSearchList[i];
                        opt.innerHTML = oSearchList[i];
                        gsSearchDropD.appendChild(opt);
                    }
                    
                } else {
                    gsSearchDropD.style.display = 'none';
                    gsSearchBox.style.display = 'block';
                    gsSearchIcon[0].style.display = 'block';
                }
                
                // Set the Form values in the settings page: 
                gsImageType.value = oImageType;
                gsImagePos.value = oImagePos;
                gsIntTheme.value = oIntTheme;
                gsIntUnit.value = oIntUnit;
                gsBackColor.value = oBackColor;
                // gsBackFile.value = '';

                if (oImageType === 'color') {
                    document.getElementById('hidden_choice_1').style.display = 'block'
                    document.getElementById('hidden_choice_2').style.display = 'none'
                } else {
                    document.getElementById('hidden_choice_2').style.display = 'block'
                    document.getElementById('hidden_choice_1').style.display = 'none'
                };
            }
            // Construct BODY Background styling string
            if (oImageType === 'image') {
                console.log(oBackFile)
                var fileName = ' url(./static/images/' + String(oBackFile) + ') ';

                if (oImagePos === 'tiled') {
                    var posit = "repeat";
                } else {
                    var posit = "no-repeat";
                }
                var backgroundString = String(oBackColor) + String(fileName) + String(posit) + ' center center';
                console.log(backgroundString)
                document.body.style.background = backgroundString;
            } else {
                var backgroundString = String(oBackColor);
                console.log(backgroundString)
                document.body.style.background = backgroundString;
            };
            
            // Change SCSS Variables for Theme Choice and Accent Color:
            if (oIntTheme === 'light') {

                var active_text_elems = document.getElementsByClassName('active-text');
                var inactive_text_elems = document.getElementsByClassName('inactive-text');
                var stroke_2 = document.getElementsByClassName('stroke-2');

                for (var i = 0; i < active_text_elems.length; i++) {
                    if (active_text_elems[i].classList.contains('default')) {
                        active_text_elems[i].classList.remove('default');
                    } else if (active_text_elems[i].classList.contains('black')) {
                        active_text_elems[i].classList.remove('black');
                    }
                    active_text_elems[i].classList.add('light');
                  };

                  for (var i = 0; i < inactive_text_elems.length; i++) {
                    if (inactive_text_elems[i].classList.contains('default')) {
                        inactive_text_elems[i].classList.remove('default');
                    } else if (inactive_text_elems[i].classList.contains('black')) {
                        inactive_text_elems[i].classList.remove('black');
                    }
                    active_text_elems[i].classList.add('light');
                  };
                  for (var i = 0; i < stroke_2.length; i++) {
                    if (stroke_2[i].classList.contains('default')) {
                        stroke_2[i].classList.remove('default');
                    } else if (stroke_2[i].classList.contains('black')) {
                        stroke_2[i].classList.remove('black');
                    }
                    stroke_2[i].classList.add('light');
                };

            } else if (oIntTheme === 'dark') {

                var active_text_elems = document.getElementsByClassName('active-text');
                var inactive_text_elems = document.getElementsByClassName('inactive-text');
                var stroke_2 = document.getElementsByClassName('stroke-2');

                for (var i = 0; i < active_text_elems.length; i++) {
                    if (active_text_elems[i].classList.contains('light')) {
                        active_text_elems[i].classList.remove('light');
                    } else if (active_text_elems[i].classList.contains('black')) {
                        active_text_elems[i].classList.remove('black');
                    }
                    active_text_elems[i].classList.add('default');
                };
                for (var i = 0; i < inactive_text_elems.length; i++) {
                    if (inactive_text_elems[i].classList.contains('light')) {
                        inactive_text_elems[i].classList.remove('light');
                    } else if (inactive_text_elems[i].classList.contains('black')) {
                        inactive_text_elems[i].classList.remove('black');
                    }
                    inactive_text_elems[i].classList.add('default');
                };  
                for (var i = 0; i < stroke_2.length; i++) {
                    if (stroke_2[i].classList.contains('light')) {
                        stroke_2[i].classList.remove('light');
                    } else if (stroke_2[i].classList.contains('black')) {
                        stroke_2[i].classList.remove('black');
                    }
                    stroke_2[i].classList.add('default');
                    console.log(stroke_2[i].classList);
                };                  

            } else if (oIntTheme === 'black') {

                var active_text_elems = document.getElementsByClassName('active-text');
                var inactive_text_elems = document.getElementsByClassName('inactive-text');
                var stroke_2 = document.getElementsByClassName('stroke-2');

                for (var i = 0; i < active_text_elems.length; i++) {
                    if (active_text_elems[i].classList.contains('light')) {
                        active_text_elems[i].classList.remove('light');
                    } else if (active_text_elems[i].classList.contains('default')) {
                        active_text_elems[i].classList.remove('default');
                    }
                    active_text_elems[i].classList.add('black');
                };
                for (var i = 0; i < inactive_text_elems.length; i++) {
                    if (inactive_text_elems[i].classList.contains('light')) {
                        inactive_text_elems[i].classList.remove('light');
                    } else if (inactive_text_elems[i].classList.contains('default')) {
                        inactive_text_elems[i].classList.remove('default');
                    }
                    inactive_text_elems[i].classList.add('black');
                };  
                for (var i = 0; i < stroke_2.length; i++) {
                    if (stroke_2[i].classList.contains('light')) {
                        stroke_2[i].classList.remove('light');
                    } else if (inactive_text_elems[i].classList.contains('default')) {
                        stroke_2[i].classList.remove('default');
                    }
                    stroke_2[i].classList.add('black');
                };  

            } else {
                console.log(oIntTheme)
            }
            // Change Units on the Thermostat and Weather:

        }
    })};
    $( window ).on( "load", loadSettings );