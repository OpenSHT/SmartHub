(function($) {
    $.fn.htmlNumberSpinner = function () {
        
        /* default value and variables and jquery elements*/
        var defaultValue = 0, inputValue;
        var numberInput$ = $(this).find('.number-input');
        var incrementerEl$ = $(this).find('.incrementer');
        var decrementerEl$ = $(this).find('.decrementer');

        /* props - dynamic attributes */
        var minAttributeValue = $(this).attr("min");
        var maxAttributeValue = $(this).attr("max");
        var stepAttributeValue = $(this).attr("step");

        if(minAttributeValue){
            numberInput$.attr("min",+minAttributeValue);
        }

        if(maxAttributeValue){
            numberInput$.attr("max", +maxAttributeValue);
        }

        if(stepAttributeValue){
            numberInput$.attr("step", +stepAttributeValue);
        }


        /* set the default value into the input */
        inputValue = minAttributeValue ? minAttributeValue: defaultValue;
        numberInput$.val(inputValue);

        /* incrementer functionality */
        incrementerEl$.click(function () {
            var parentEl = $(this).parent();
            inputValue = parentEl.find('.number-input').val();
            if(maxAttributeValue){
                if(maxAttributeValue==inputValue){
                    return;
                }
            }
            if(stepAttributeValue){
                inputValue = parentEl.find('.number-input').val();
                parentEl.find('.number-input').val((+inputValue)+(+stepAttributeValue));
                return;
            }
            inputValue = parentEl.find('.number-input').val();
            parentEl.find('.number-input').val(++inputValue);
        });

        /* decrementer functionality */
        decrementerEl$.click(function () {
            var parentEl = $(this).parent();
            inputValue = parentEl.find('.number-input').val();
            if(minAttributeValue){
                if(minAttributeValue==inputValue){
                    return;
                }
            }
            if(stepAttributeValue){
                inputValue = parentEl.find('.number-input').val();
                parentEl.find('.number-input').val((+inputValue)-(+stepAttributeValue));
                return;
            }
            inputValue = parentEl.find('.number-input').val();
            parentEl.find('.number-input').val(--inputValue);
        })

        numberInput$.change(function () {
            if(!maxAttributeValue || !minAttributeValue) return;
            var currentValue = $(this).val();
            if((+currentValue)>(+maxAttributeValue)){
                $(this).val(maxAttributeValue)
                return;
            }
            if((+currentValue)<(+minAttributeValue)){
                $(this).val(minAttributeValue)
                return;
            }
        })

    };

    $.fn.getSpinnerValue = function () {
        return $(this).find('.number-input').val();
    }

}(jQuery));
