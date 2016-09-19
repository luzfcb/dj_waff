$(document).ready(
    function () {
        "use strict";
        var other_choice = $('[data-choice-fields-other]');
        var last_radio_choice_input = other_choice.parent().parent().eq(0).find('input:radio');
        var uncheck_check_last = function (selector, last_radio_choice_input_id) {
            $('[data-choice-fields="' + selector + '"]').each(function () {
                if ($(this).attr('id') === last_radio_choice_input_id) {
                    $(this).prop('checked', true);
                    console.log('is last_radio_choice_input_id');
                }
                else {
                    $(this).prop('checked', false);
                }

            });
        };

        other_choice.on('click', function () {
            uncheck_check_last(last_radio_choice_input.attr('data-choice-fields'), last_radio_choice_input.attr('id'));
            // last_radio_choice_input.prop('checked', true);
            console.log('clock');
        });
        other_choice.on('change', function () {
            uncheck_check_last(last_radio_choice_input.attr('data-choice-fields'), last_radio_choice_input.attr('id'));
            // last_radio_choice_input.prop('checked', true);
        });
    }
);
