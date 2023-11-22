$(document).ready(function() {

    $(document).keydown(function(event) {

        if (event.keyCode === 39) { // Right arrow key
//             $(this).trigger('click');
             $('.oe_list_header_many2one oe_sortable sortup').trigger('click');

//            event.preventDefault(); // Prevent default behavior
//
//            var $many2oneFields = $('.oe_form_field_many2one input');
//            var $tableRows = $('.oe_form_field_one2many_list_row_add');
//
//            $many2oneFields.each(function() {
//                $(this).focus(); // Focus on the input field to display the dropdown list
//            });
//
//            $tableRows.each(function() {
//                $(this).find('.oe_list_field_many2one').click(); // Trigger the click event on the Many2One field to display the dropdown list
//            });
        }
    });
});
