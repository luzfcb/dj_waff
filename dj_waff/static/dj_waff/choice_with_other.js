$(document).ready(
    function () {
        "use strict";
        var choice_with_other_wrappers = $(".choice_with_other_wrapper");
        var uncheck_check_last = function (selector, last_radio_choice_input_id) {
            $('input[name="' + selector + '"]').each(function () {
                if ($(this).attr('id') === last_radio_choice_input_id) {
                    $(this).prop('checked', true);
                }
                else {
                    $(this).prop('checked', false);
                }
            });
        };
        choice_with_other_wrappers.each(function () {
            var other_choice = $(this).find('[data-choice-fields-other]');
            var last_radio_choice_input = $(this).find('input:radio').last();
            other_choice.on('click', function () {
                uncheck_check_last(last_radio_choice_input.attr('name'), last_radio_choice_input.attr('id'));
                console.log('clock');
            });
            // other_choice.on('change', function () {
            //     uncheck_check_last(last_radio_choice_input.attr('name'), last_radio_choice_input.attr('id'));
            //     // last_radio_choice_input.prop('checked', true);
            // });
        });
    }
);
