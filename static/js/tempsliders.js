// Initialize a new plugin instance for all "range" classes

// $('input[type="range"]').rangeslider({
//     polyfill: false,

//     // Default CSS classes
//     rangeClass: 'rangeslider',
//     disabledClass: 'rangeslider--disabled',
//     horizontalClass: 'rangeslider--horizontal',
//     verticalClass: 'rangeslider--vertical',
//     fillClass: 'rangeslider__fill',
//     handleClass: 'rangeslider__handle',

//     // Callback function
//     onInit: function() {
//         var input = document.getElementById("sp_value");
//         this.value = input.innerHTML
//     },

//     // Callback function
//     onSlide: function(position, value) {
//         var output = document.getElementById("sp_value");
//     	output.innerHTML = this.value;
//     },

//     // Callback function
//     onSlideEnd: function(position, value) {
//     	var $handle = this.$range.find('.rangeslider__handle__value');
//     	var output = document.getElementById("sp_value");
//     	output.innerHTML = this.value;
//         $handle.text(this.value);

//         $.ajax({
// 	        url: '/_sp_changed',
// 	        type: "POST",
// 	        data: this.value,
// 	        processData: false,
// 	        contentType: "charset=UTF-8",
// 	        success: function(response) {
// 	            console.log(response);
// 	        },
// 	        error: function(error) {
// 	            console.log(error);
// 	        }
//     	});
//     }
// });

// SINGLE HANDLE TEMPERATURE SLIDER:
$( function spSlider() {
    // var handle1 = $( "#custom-handle-1" );
    // var handle2 = $( "#custom-handle-2" );

    $( "#sp-range-slider" ).slider({
        range: false,
        min: 15,
        max: 30,
        step: 0.5,
        value: 22,
        // create: function() {
        //     handle1.text( $( this ).slider( "values", 0 ) );
        //     handle2.text( $( this ).slider( "values", 1 ) );
        //   },
        start: function( event, ui ) {
            var input = document.getElementById("sp_value");
            this.value = input.innerHTML
        },
        slide: function( event, ui ) {
            
            $( "#sp_value" ).html(ui.value);
        },
        stop: function( event, ui ) {
            console.log(ui.value)
            $.ajax({
                url: '/_sp_changed',
                type: "POST",
                data: {
                    home_temp: ui.value
                },
                success: function(response) {
                    console.log(response);
                },
                error: function(error) {
                    console.log(error);
                }
            });
        }
    });
    // $( "#sp_value" ).html($( "#sp-range-slider" ).slider( "value"));
} );
